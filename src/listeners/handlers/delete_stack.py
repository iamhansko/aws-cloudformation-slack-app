import boto3

cloudformation = boto3.client('cloudformation')

def handler(say, body, context):
  try:
    selected_stack_name = body['state']['values']['stack_select_block']['stack_select']['selected_option']['text']['text']
    
    cloudformation.delete_stack(
      StackName=selected_stack_name
    )

    say(
        blocks=[
          {
            'type': 'section',
            'text': {
              'type': 'mrkdwn',
              'text': f'Stack {selected_stack_name}을 삭제합니다.',
            },
          },
        ],
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