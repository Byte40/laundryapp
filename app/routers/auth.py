#This API was developed by Alex Mutonga
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app import database, schemas, models, utils
from app.oauth2 import authenticate_user, create_access_token

router = APIRouter(tags=['Authentication'])

async def authenticate_user(username: str, password: str, user_type: str, db: Session = Depends(database.get_db)):
    user = None

    if user_type == "admin":
        user = db.query(models.Admin).filter(models.Admin.email == username).first()
    elif user_type == "courier":
        user = db.query(models.Courier).filter(models.Courier.email == username).first()
    elif user_type == "customer":
        user = db.query(models.Customer).filter(models.Customer.email == username).first()
    elif user_type == "laundromat":
        user = db.query(models.Laundromat).filter(models.Laundromat.email == username).first()

    if not user:
        return None  # Return None instead of False

    if not utils.verify(password, user.password):
        return None  # Return None instead of False

    return user

@router.post('/customerlogin', response_model=schemas.Token)
async def login(user_credentials: schemas.CustomerLogin, db: Session = Depends(database.get_db)):

    user = await authenticate_user(user_credentials.email, user_credentials.password, "customer", db)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

    access_token = create_access_token(data={"user_id": user.customer_id, "user_type": "customer"})

    return {"access_token": access_token, "token_type": "bearer"}


@router.post('/laundromatlogin', response_model=schemas.Token)
async def login(user_credentials: schemas.LaundromatLogin, db: Session = Depends(database.get_db)):

    user = await authenticate_user(user_credentials.email, user_credentials.password, "laundromat", db)

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

    access_token = create_access_token(data={"user_id": user.laundromat_id, "user_type": "laundromat"})

    return {"access_token": access_token, "token_type": "bearer"}


@router.post('/courierlogin', response_model=schemas.Token)
async def login(user_credentials: schemas.CourierLogin, db: Session = Depends(database.get_db)):

    user = await authenticate_user(user_credentials.email, user_credentials.password, "courier", db)

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

    access_token = create_access_token(data={"user_id": user.courier_id, "user_type": "courier"})

    return {"access_token": access_token, "token_type": "bearer"}


@router.post('/adminlogin', response_model=schemas.Token)
async def login(user_credentials: schemas.AdminLogin, db: Session = Depends(database.get_db)):

    user = await authenticate_user(user_credentials.email, user_credentials.password, "admin", db)

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

    access_token = create_access_token(data={"user_id": user.admin_id, "user_type": "admin"})

    return {"access_token": access_token, "token_type": "bearer"}
