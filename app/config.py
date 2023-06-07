#This API was developed by Alex Mutonga
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    class Config:
        env_file =".env"


class TwilioSettings(BaseSettings):
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str

    class Config:
        env_prefix = "TWILIO_"


settings = Settings()
twilio_settings = TwilioSettings()

def load_settings():
    settings = Settings()
    settings.twilio = TwilioSettings()
    return settings
