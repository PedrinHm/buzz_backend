import firebase_admin
from firebase_admin import credentials, messaging
import os
import json
from fastapi import HTTPException

# Carregar as credenciais do Firebase a partir da variável de ambiente
firebase_credentials = os.getenv('FIREBASE_CREDENTIALS_JSON')

# Verificar se as credenciais foram fornecidas
if not firebase_credentials:
    raise ValueError("As credenciais do Firebase não foram fornecidas ou estão vazias. Certifique-se de definir a variável de ambiente 'FIREBASE_CREDENTIALS_JSON'.")

try:
    # Carregar as credenciais em formato JSON
    cred_dict = json.loads(firebase_credentials)
    cred = credentials.Certificate(cred_dict)
except json.JSONDecodeError as e:
    raise ValueError(f"Erro ao decodificar as credenciais do Firebase: {str(e)}")

# Inicializar o aplicativo Firebase somente se ainda não estiver inicializado
if not firebase_admin._apps:
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
        raise HTTPException(status_code=500, detail=f"Falha ao enviar notificação: {str(e)}")
