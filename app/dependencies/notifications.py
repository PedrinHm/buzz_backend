import httpx
from fastapi import HTTPException

# Defina a URL e a chave do servidor FCM
FCM_SERVER_KEY = 'BMNwFmQ0n47NfSNvlnR53Snqbh37sJhpX4p3jIPQhcNUSYaznnhy95sqIVtDm3ylSsvBwJ0y2UsWg-3dCY-llTM'  
FCM_URL = 'https://fcm.googleapis.com/fcm/send'

async def send_push_notification(token: str, title: str, body: str):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'key={FCM_SERVER_KEY}',
    }
    payload = {
        'to': token,
        'notification': {
            'title': title,
            'body': body,
        },
        'priority': 'high',
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(FCM_URL, json=payload, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to send notification")
        return response.json()
