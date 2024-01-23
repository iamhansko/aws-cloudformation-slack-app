import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from listeners.handlers import describe_stack_events, delete_stack

def listener(app):
    app.action("stack_events")(
        ack=respond_to_actions_within_3_seconds,  
        lazy=[describe_stack_events.handler]  
    )
    app.action("stack_delete")(
        ack=respond_to_actions_within_3_seconds,  
        lazy=[delete_stack.handler]  
    )

def respond_to_actions_within_3_seconds(ack):
    ack()