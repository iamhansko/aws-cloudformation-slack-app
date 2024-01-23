import boto3

cloudformation = boto3.client('cloudformation')

completed_status = [
  'CREATE_COMPLETE',
  'DELETE_COMPLETE',
  'DELETE_SKIPPED',
  'UPDATE_COMPLETE',
  'IMPORT_COMPLETE',
  'IMPORT_ROLLBACK_COMPLETE',
  'UPDATE_ROLLBACK_COMPLETE',
  'ROLLBACK_COMPLETE'
]
inprogress_status = [
  'CREATE_IN_PROGRESS',
  'DELETE_IN_PROGRESS',
  'UPDATE_IN_PROGRESS',
  'IMPORT_IN_PROGRESS',
  'IMPORT_ROLLBACK_IN_PROGRESS',
  'UPDATE_ROLLBACK_IN_PROGRESS',
  'ROLLBACK_IN_PROGRESS',
  'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS'
]
failed_status = [
  'CREATE_FAILED',
  'DELETE_FAILED',
  'UPDATE_FAILED',
  'IMPORT_FAILED',
  'IMPORT_ROLLBACK_FAILED',
  'UPDATE_ROLLBACK_FAILED',
  'ROLLBACK_FAILED'
]

def stack_event_transform(stack_event):
  stack_resource_id = stack_event['LogicalResourceId']
  stack_resource_type = stack_event['ResourceType']
  stack_status = stack_event['ResourceStatus']
  if stack_event['ResourceStatus'] in completed_status or '_COMPLETE' in stack_event['ResourceStatus']:
    stack_status = f':white_check_mark: `{stack_status}`'
  elif stack_event['ResourceStatus'] in failed_status or '_FAILED' in stack_event['ResourceStatus']:
    stack_status = f':x: `{stack_status}`'
  else :
    stack_status = f':gear: `{stack_status}`'
  stack_status_reason = '' if stack_event.get('ResourceStatusReason') is None else '- ' + stack_event.get('ResourceStatusReason')
  return {
    'type': 'section',
    'text': {
      'type': 'mrkdwn',
      'text': f'*{stack_resource_type}:{stack_resource_id}* {stack_status} {stack_status_reason}',
    }
  }

def handler(say, body, context):
  try:
    selected_stack_name = body['state']['values']['stack_select_block']['stack_select']['selected_option']['text']['text']

    describe_stack_events_response = cloudformation.describe_stack_events(
      StackName=selected_stack_name
    )

    stack_events = list(map(stack_event_transform, describe_stack_events_response['StackEvents']))

    iteration = len(stack_events) // 50
    for i in range(iteration+1):
      if i == iteration:
        if len(stack_events) % 50 != 0:
          say(
              blocks=stack_events[50*i:],
              thread_ts=body['message']['ts']
          )
      else:
        say(
            blocks=stack_events[50*i:50*(i+1)],
            thread_ts=body['message']['ts']
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
        thread_ts=body['message']['ts']
    )