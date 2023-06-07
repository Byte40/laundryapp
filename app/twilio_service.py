import os
from twilio.rest import Client
from fastapi import HTTPException
from app.config import settings


def send_verification_code(phone_number: str):
    try:
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        verification = client.verify.v2.services(settings.twilio_verify_sid) \
            .verifications \
            .create(to=phone_number, channel="sms")
        return verification.status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def verify_code(phone_number: str, code: str):
    try:
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        verification_check = client.verify.v2.services(settings.twilio_verify_sid) \
            .verification_checks \
            .create(to=phone_number, code=code)
        return verification_check.status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
