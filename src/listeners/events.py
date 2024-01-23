import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from listeners.handlers import create_stack

def listener(app):
    app.event("app_mention")(
        ack=respond_to_events_within_3_seconds,  
        lazy=[create_stack.handler]  
    )

def respond_to_events_within_3_seconds(ack):
    ack()