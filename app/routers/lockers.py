# This API was developed by Alex Mutonga
import random
from sqlalchemy import func
import string
from typing import List
from fastapi import status, HTTPException, Depends, APIRouter, Request
from sqlalchemy.orm import Session
from app import models, schemas, oauth2
from app.database import get_db

router = APIRouter(
    prefix="/lockers",
    tags=['lockers']
)

# Creating a Locker
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.LockerOut)
async def create_locker(
    locker: schemas.LockerCreate,
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):

    # Check if the current user is an admin or laundromat
    if current_user.user_type not in ["admin", "laundromat"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")

    # Check if locker_number already exists
    if db.query(models.Locker).filter(models.Locker.locker_number == locker.locker_number).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Locker number already exists")

    new_locker = models.Locker(**locker.dict())
    db.add(new_locker)
    db.commit()
    db.refresh(new_locker)

    # Convert new_locker object to dictionary
    new_locker_dict = new_locker.__dict__
    new_locker_dict.pop("_sa_instance_state", None)

    return new_locker_dict

# Enable customers to book a locker
# Function to generate a random locker code
def generate_locker_code():
    code_length = 6
    characters = string.digits
    return ''.join(random.choices(characters, k=code_length))

@router.post("/{locker_id}/book", status_code=status.HTTP_200_OK)
def book_locker(
    locker_id: int,
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    # Check if the current user is a customer
    if current_user.user_type != "customer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized Access")

    # Fetch the locker from the database
    locker = db.query(models.Locker).get(locker_id)
    if not locker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Locker with id: {locker_id} not found")

    # Check if the locker is already booked
    if locker.status == models.LockerStatus.OCCUPIED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Locker is already booked")

    # Fetch the customer's most recent order
    customer_orders = db.query(models.Order).filter(models.Order.customer_id == current_user.customer_id).\
        order_by(models.Order.created_at.desc()).all()
    if not customer_orders:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No orders found for the customer")

    recent_order = customer_orders[0]  # Get the most recent order

    # Associate the locker with the recent order
    recent_order.locker_id = locker.locker_id

    # Generate a code for the locker
    code = generate_locker_code()
    locker.code = code
    recent_order.locker_code = code

    # Update the locker status to booked
    locker.status = models.LockerStatus.OCCUPIED

    db.commit()

    return {"message": f"Locker with id: {locker_id} successfully booked by customer", "code": code}

# Unlocking system by the customer
@router.post("/{locker_id}/unlock", status_code=status.HTTP_200_OK)
async def unlock_locker(
    locker_id: int,
    request: Request,
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    # Parse the request body as JSON
    request_data = await request.json()
    code = request_data.get("code")

    # Check if the current user is a customer
    if current_user.user_type != "customer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized Access")

    # Fetch the locker from the database and check if it exists
    current_locker = db.query(models.Locker).filter(models.Locker.locker_id == locker_id).first()
    if not current_locker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Locker with id: {locker_id} not found")

    # Check if the locker is occupied
    if current_locker.status != models.LockerStatus.OCCUPIED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Locker is not occupied")

    # Check if the entered code matches the generated code
    matching_locker = db.query(models.Locker).filter(func.lower(models.Locker.code) == func.lower(code)).first()
    if not matching_locker:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code. Please try again.")

    # Unlock the locker
    current_locker.status = models.LockerStatus.AVAILABLE
    db.commit()

    return {"message": f"Locker with id: {locker_id} successfully unlocked by customer"}

#Locking System By the customer
@router.post("/{locker_id}/lock", status_code=status.HTTP_200_OK)
async def lock_locker(
    locker_id: int,
    request: Request,
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    # Parse the request body as JSON
    request_data = await request.json()
    code = request_data.get("code")

    # Check if the current user is a customer
    if current_user.user_type != "customer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized Access")

    # Fetch the locker from the database and check if it exists
    locker = db.query(models.Locker).get(locker_id)
    if not locker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Locker with id: {locker_id} not found")

    # Check if the locker is available
    if locker.status != models.LockerStatus.AVAILABLE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Locker is not available")

    # Check if the entered code matches the code used to unlock the locker
    if code != locker.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code. Please try again.")

    # Lock the locker
    locker.status = models.LockerStatus.OCCUPIED
    db.commit()

    return {"message": f"Locker with id: {locker_id} successfully locked by customer"}

# Fetching all lockers
@router.get("/", response_model=List[schemas.LockerOut])
def get_all_lockers(current_user: schemas.TokenData = Depends(oauth2.get_current_user),
                    db: Session = Depends(get_db)) -> List[schemas.LockerOut]:
    # Check if the current user is an admin
    if current_user.user_type != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")

    lockers = db.query(models.Locker).all()
    return lockers

# Fetching Available Lockers
@router.get("/available", response_model=List[schemas.LockerOut])
def get_available_lockers(current_user: schemas.TokenData = Depends(oauth2.get_current_user),
                          db: Session = Depends(get_db)) -> List[schemas.LockerOut]:
    # Check if the current user is a customer, laundromat, or admin
    if current_user.user_type not in ["customer", "laundromat", "admin"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")

    available_lockers = db.query(models.Locker).filter(models.Locker.status == models.LockerStatus.AVAILABLE).all()

    if len(available_lockers) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No lockers available")

    return available_lockers

#  Route for getting all occupied Lockers
@router.get("/occupied", response_model=List[schemas.LockerOut])
def get_occupied_lockers(
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
) -> List[schemas.LockerOut]:
    # Check if the current user is an admin, laundromat, or courier
    if current_user.user_type not in ["admin", "laundromat", "courier"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")

    occupied_lockers = db.query(models.Locker).filter(models.Locker.status == models.LockerStatus.OCCUPIED).all()
    return occupied_lockers

    # ocupied_lockers = db.query(models.Locker).filter(models.LockerStatus.OCCUPIED).all()
    # return ocupied_lockers

# Enable customers to retrieve the lockers they have booked.
@router.get("/booked", response_model=List[schemas.LockerOut])
def get_booked_lockers(
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
) -> List[schemas.LockerOut]:
    # Check if the current user is a customer
    if current_user.user_type != "customer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")

    booked_lockers = db.query(models.Locker).filter(
        models.Locker.status == models.LockerStatus.OCCUPIED,
        models.Customer.customer_id == current_user.customer_id
    ).all()

    return booked_lockers

# Route for Deleting lockers
@router.delete("/{locker_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_locker(
                 locker_id: int,
                 current_user: schemas.TokenData = Depends(oauth2.get_current_user),
                 db: Session = Depends(get_db)):
    # Check if the current user is an admin or laundromat
    if current_user.user_type not in ["admin", "laundromat"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")
    
    locker = db.query(models.Locker).get(locker_id)
    if not locker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Locker with id: {locker_id} not found")
    
    db.delete(locker)
    db.commit()
    return {"message": f"Locker with id: {id} successfully deleted"}