import firebase_admin
from firebase_admin import credentials, messaging
import os
import json
from fastapi import HTTPException

firebase_credentials = os.getenv('FIREBASE_CREDENTIALS_JSON')
cred_dict = json.loads(firebase_credentials)
cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)

async def send_push_notification(token: str, title: str, body: str):
    # Cria a mensagem de notificação
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
    )

    # Envia a notificação usando o Firebase Admin SDK
    try:
        response = messaging.send(message)
        return {"success": True, "message_id": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")
