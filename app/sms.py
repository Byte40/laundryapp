from twilio.rest import Client
from fastapi import HTTPException
from app.config import settings

def send_sms(to: str, body: str):
    try:
        client = Client(settings.twilio.account_sid, settings.twilio.auth_token)
        message = client.messages.create(
            body=body,
            from_=settings.twilio.phone_number,
            to=to
        )
        return message
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
