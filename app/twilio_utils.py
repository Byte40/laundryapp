from twilio.rest import Client
from app.config import settings


def send_sms(to: str, body: str):
    account_sid = settings.twilio.TWILIO_ACCOUNT_SID
    auth_token = settings.twilio.TWILIO_AUTH_TOKEN
    verify_sid = settings.twilio.TWILIO_VERIFY_SID
    phone_number = settings.twilio.TWILIO_PHONE_NUMBER

    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=body,
        from_=phone_number,
        to=to
    )

    return message.sid

