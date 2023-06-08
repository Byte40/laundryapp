# This API was developed by Alex Mutonga
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app import schemas, database, utils
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.models import Customer, Laundromat, Courier, Admin

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/login')

# SECRET_key
# Algorithm
# Expiration time

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "user_id": data["user_id"], "user_type": data["user_type"]})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("user_id")
        user_type: str = payload.get("user_type")
        email: str = payload.get("email")  # Extract the email from the payload

        if id is None or user_type is None:
            raise credentials_exception

        token_data = schemas.TokenData(id=id, user_type=user_type, email=email)  # Include the email in TokenData
    except JWTError:
        raise credentials_exception
    except Exception as e:
        print("Exception in verify_access_token:", e)
        raise credentials_exception

    return token_data

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail="Could not validate credentials",
                                          headers={"WWW-Authenticate": "Bearer"})
    token_data = verify_access_token(token, credentials_exception)
    user = None

    if token_data:
        if token_data.user_type == "admin":
            user = db.query(Admin).filter(Admin.admin_id == token_data.id).first()
        elif token_data.user_type == "courier":
            user = db.query(Courier).filter(Courier.courier_id == token_data.id).first()
            token_data.courier_id = user.courier_id  # Include the courier_id in TokenData
        elif token_data.user_type == "customer":
            user = db.query(Customer).filter(Customer.customer_id == token_data.id).first()
            token_data.customer_id = user.customer_id  # Include the customer_id in TokenData
        elif token_data.user_type == "laundromat":
            user = db.query(Laundromat).filter(Laundromat.laundromat_id == token_data.id).first()
            token_data.laundromat_id = user.laundromat_id  # Include the laundromat_id in TokenData

    if not user:
        raise credentials_exception

    return token_data

async def authenticate_user(username: str, password: str, user_type: str, db: Session = Depends(database.get_db)):
    user = None

    if user_type == "admin":
        user = db.query(Admin).filter(Admin.email == username).first()
    elif user_type == "courier":
        user = db.query(Courier).filter(Courier.email == username).first()
    elif user_type == "customer":
        user = db.query(Customer).filter(Customer.email == username).first()
    elif user_type == "laundromat":
        user = db.query(Laundromat).filter(Laundromat.email == username).first()

    if not user:
        return False
    if not utils.verify(password, user.password):
        return False

    # Include the user's ID in the data dictionary
    data = {"id": user.customer_id, "user_type": user_type}
    token = create_access_token(data)

    return token

async def get_current_active_user(current_user: Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not authenticated")
    return current_user