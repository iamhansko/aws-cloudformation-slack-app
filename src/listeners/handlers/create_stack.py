import os
import json
import requests
import boto3
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import *

s3 = boto3.client('s3')
cloudformation = boto3.client('cloudformation')
INSTALLATION_S3_BUCKET_NAME = os.getenv('INSTALLATION_S3_BUCKET_NAME')

def stack_transform(stack):
  stack_name = stack['StackName']
  return {
    'text': {
      'type': 'plain_text',
      'text': f'{stack_name}',
      'emoji': True
    },
    'value': stack['StackId']
  }

def list_stacks():
  list_stacks_response = cloudformation.list_stacks(
    StackStatusFilter=[
      'CREATE_IN_PROGRESS',
      'CREATE_FAILED',
      'CREATE_COMPLETE',
      'ROLLBACK_IN_PROGRESS',
      'ROLLBACK_FAILED',
      'ROLLBACK_COMPLETE',
      'DELETE_IN_PROGRESS',
      'DELETE_FAILED',
      'UPDATE_IN_PROGRESS',
      'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS',
      'UPDATE_COMPLETE',
      'UPDATE_FAILED',
      'UPDATE_ROLLBACK_IN_PROGRESS',
      'UPDATE_ROLLBACK_FAILED',
      'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS',
      'UPDATE_ROLLBACK_COMPLETE',
      'REVIEW_IN_PROGRESS',
      'IMPORT_IN_PROGRESS',
      'IMPORT_COMPLETE',
      'IMPORT_ROLLBACK_IN_PROGRESS',
      'IMPORT_ROLLBACK_FAILED',
      'IMPORT_ROLLBACK_COMPLETE'
    ]
  )
  return list(map(stack_transform, list_stacks_response['StackSummaries']))

def handler(say, event, body, context):
  try:
    if event.get('files') is None or len(event['files']) == 0 or (event['files'][0]['filetype'] != 'yaml' and event['files'][0]['filetype'] != 'yml' and event['files'][0]['filetype'] != 'json'):
      stacks = list_stacks()

      say(
        blocks=[
          {
            'type': 'section',
            'text': {
              'type': 'mrkdwn',
              'text': f'첨부된 템플릿 파일(.yaml, .yml, .json)이 없습니다.',
            }
          },
          {
            'type': 'input',
            'block_id': 'stack_select_block',
            'element': {
              'type': 'static_select',
              'placeholder': {
                'type': 'plain_text',
                'text': 'Select a Stack',
                'emoji': True
              },
              'options': stacks,
              'action_id': 'stack_select'
            },
            'label': {
              'type': 'plain_text',
              'text': 'Stack',
              'emoji': True
            }
          },
          {
            'type': 'actions',
            'elements': [
              {
                'type': 'button',
                'text': {
                  'type': 'plain_text',
                  'text': 'View Events',
                  'emoji': True
                },
                'value': 'view_events_button_click',
                'action_id': 'stack_events'
              },
              {
                'type': 'button',
                'text': {
                  'type': 'plain_text',
                  'text': 'Delete',
                  'emoji': True
                },
                'value': 'delete_stack_button_click',
                'action_id': 'stack_delete'
              }
            ]
          }
        ],
        thread_ts=event['ts']
      )
    else:
      team_id = context['team_id']
      s3_objects = s3.list_objects(
          Bucket = INSTALLATION_S3_BUCKET_NAME
      )
      filtered_objects = [ obj['Key'] for obj in s3_objects['Contents'] if f'-{team_id}/bot-latest' in obj['Key'] ]
      object_key = filtered_objects[0]
      res = s3.get_object(
          Bucket = INSTALLATION_S3_BUCKET_NAME,
          Key = object_key,
      )
      content = res['Body'].read()
      secrets = json.loads(content)
      workspace_bot_token = secrets['bot_token']

      file_name = event['files'][0]['title'].replace('.'+event['files'][0]['filetype'], '')
      file_url = event['files'][0]['url_private']
      file_contents = requests.get(file_url, headers={'Authorization': f'Bearer {workspace_bot_token}'})

      timezone_kst = timezone(timedelta(hours=9))
      now = datetime.now(timezone_kst)
      month = ('0' + str(now.month))[-2:]
      day = ('0' + str(now.day))[-2:]
      hour = ('0' + str(now.hour))[-2:]
      minute = ('0' + str(now.minute))[-2:]

      cloudformation.create_stack(
        StackName=f'stack-{file_name}-{now.year}{month}{day}{hour}{minute}',
        TemplateBody=file_contents.text,
        DisableRollback=False,
        Capabilities=[
            'CAPABILITY_NAMED_IAM'
        ]
      )

      stacks = list_stacks()
        
      say(
          blocks=[
            {
              'type': 'section',
              'text': {
                'type': 'mrkdwn',
                'text': f'CloudFormation Stack을 생성합니다.',
              },
            },
            {
              'type': 'input',
              'block_id': 'stack_select_block',
              'element': {
                'type': 'static_select',
                'placeholder': {
                  'type': 'plain_text',
                  'text': 'Select a Stack',
                  'emoji': True
                },
                'options': stacks,
                'action_id': 'stack_select'
              },
              'label': {
                'type': 'plain_text',
                'text': 'Stack',
                'emoji': True
              }
            },
            {
              'type': 'actions',
              'elements': [
                {
                  'type': 'button',
                  'text': {
                    'type': 'plain_text',
                    'text': 'View Events',
                    'emoji': True
                  },
                  'value': 'view_events_button_click',
                  'action_id': 'stack_events'
                },
                {
                  'type': 'button',
                  'text': {
                    'type': 'plain_text',
                    'text': 'Delete',
                    'emoji': True
                  },
                  'value': 'delete_stack_button_click',
                  'action_id': 'stack_delete'
                }
              ]
            }
          ],
          thread_ts=event['ts']
      )
  except Exception as error:
    say(
        blocks=[
          {
            'type': 'section',
            'text': {
              'type': 'mrkdwn',
              'text': f'에러가 발생하였습니다. {error}',
            },
          },
        ],
        thread_ts=event['ts']
    )