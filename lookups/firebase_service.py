import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
from decouple import config

firebase_json = json.loads(
    config('FIREBASE_CREDENTIALS')
)

cred=credentials.Certificate(firebase_json)

firebase_admin.initialize_app(cred)

def send_push_notification(token,user_name, title, body):
    message=messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=f"{user_name} {body}"
        ),
        token=token
    )
    response=messaging.send(message)
    return response