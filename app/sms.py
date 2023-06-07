from fastapi import HTTPException
from app.twilio_service import send_verification_code, verify_code


def send_sms_verification(to: str):
    try:
        status = send_verification_code(to)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def verify_sms_code(phone_number: str, code: str):
    try:
        status = verify_code(phone_number, code)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


