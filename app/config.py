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
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str
    twilio_verify_sid: str  # Add this line

    class Config:
        env_file = ".env"


settings = Settings()






# class TwilioSettings(BaseSettings):
#     twilio_account_sid: str
#     twilio_auth_token: str
#     twilio_phone_number: str


# def load_settings():
#     settings = Settings()
#     twilio_settings = TwilioSettings()
#     settings.twilio_settings = twilio_settings
#     return settings


# settings = load_settings()
# twilio_settings = settings.twilio_settings
