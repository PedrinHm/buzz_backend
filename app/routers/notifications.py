from fastapi import APIRouter, HTTPException
from app.dependencies.notifications import send_push_notification

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"]
)

router = APIRouter()

@router.post("/send-notification/")
async def notify_user(token: str, title: str, message: str):
    try:
        result = await send_push_notification(token, title, message)
        return {"status": "Notification sent", "result": result}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
