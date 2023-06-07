#This API was developed by Alex Mutonga
from typing import List
from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from app import models, oauth2
from app import schemas, utils
from app.database import get_db
from app.models import Courier, CourierDeletionRequest 
 
router=APIRouter(
    prefix="/courier",
    tags=['courier']
)


# Creating a new courier
@router.post("/", status_code=status.HTTP_201_CREATED, response_model= schemas.CourierOut)
def create_courier(courier: schemas.CourierCreate, db: Session = Depends(get_db)):

      # Check if email already exists
    if db.query(models.Courier).filter(models.Courier.email == courier.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    # Check if phone number already exists
    if db.query(models.Courier).filter(models.Courier.phone_number == courier.phone_number).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone number already exists")
    
    # Check if phone number already exists
    if db.query(models.Courier).filter(models.Courier.vehicle_reg_no == courier.vehicle_reg_no).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vehicle already registerd")
    
    #hash the password - courierts.password
    hashed_password = utils.hash(courier.password)
    courier.password = hashed_password

    new_courier = models.Courier(**courier.dict())
    db.add(new_courier)
    db.commit()
    db.refresh(new_courier)

    # Convert new_couriert object to dictionary
    new_courier_dict = new_courier.__dict__

    # Remove the "_sa_instance_state" key from the dictionary
    new_courier_dict.pop("_sa_instance_state", None)

    return new_courier_dict

# Fetching all Couriers
@router.get("/", status_code=status.HTTP_200_OK, response_model=List[schemas.CourierOut])
def get_courier(
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
) -> List[schemas.CourierOut]:
    
    # Courier fetching thier own info
    if current_user.user_type == "courier":
        if current_user.courier_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Courier ID not found in token")
        #check if current_user_id and id requested match
        courier_id = int(current_user.courier_id)
        courier = db.query(models.Courier).filter(models.Courier.courier_id == courier_id).first()
        if not courier:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Courier not found")
        return [courier]

    # fetching all couriers
    if current_user.user_type in ["admin", "laundromat"]:
        couriers = db.query(models.Courier).all()
        return couriers

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

# Get courier by id
@router.get('/{courier_id}', response_model=schemas.CourierOut, status_code=status.HTTP_201_CREATED)
def get_courier(
    courier_id: int,
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db),
) -> schemas.CourierOut:
    # Check whether current_user is admin or laundromat
    if current_user.user_type in ["admin", "laundromat"]:
        courier = db.query(models.Courier).filter(models.Courier.courier_id == courier_id).first()
        if not courier:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Courier with id: {courier_id} does not exist")
        return courier
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

# Update courier
@router.put('/{courier_id}', response_model=schemas.CourierOut, status_code=status.HTTP_201_CREATED)
def update_courier(
    courier_id: int,
    courier: schemas.CourierUpdate,
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db),
) -> schemas.CourierOut:
    # Check whether current_user is courier
    if current_user.user_type == "courier":
        current_courier = db.query(models.Courier).filter(models.Courier.courier_id == courier_id).first()
        if not current_courier:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Courier with id: {courier_id} does not exist")

        # Check if the current courier ID matches the user's courier ID
        if current_courier.courier_id != current_user.courier_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

        # Update the courier fields
        for field, value in courier.dict(exclude_unset=True).items():
            # Check if the field is 'password'
            if field == 'password' and value:
                hashed_password = utils.hash(courier.password)  # Hash the new password
                setattr(current_courier, field, hashed_password)
            else:
                setattr(current_courier, field, value)

        # Commit changes to the database
        db.commit()
        db.refresh(current_courier)

        # Create the response model
        courier_out = schemas.CourierOut(
            courier_id=current_courier.courier_id,
            name=current_courier.name,
            phone_number=current_courier.phone_number,
            email=current_courier.email,
            vehicle_reg_no=current_courier.vehicle_reg_no
        )

        return courier_out
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

# Account delete Request by courier
@router.delete('/{courier_id}/request', status_code=status.HTTP_200_OK)
def Request_courier_acount_deletion(
    courier_id: int,
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db),
):
    # Check whether current_user is courier
    if current_user.user_type == "courier":
        current_courier = db.query(models.Courier).filter(models.Courier.courier_id == courier_id).first()
        if not current_courier:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Courier with id: {courier_id} does not exist")
        
        # Check if the current courier ID matches the user's courier ID
        if current_courier.courier_id != current_user.courier_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
        
        # Check if the Deletion Requests already exists for this courier
        deletion_request = db.query(models.CourierDeletionRequest).filter(models.CourierDeletionRequest.id == courier_id).first()
        if deletion_request:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deletion Request already exists")
        
        # Create a new deletion request
        deletion_request = models.CourierDeletionRequest(
            courier_id=courier_id
        )
        db.add(deletion_request)
        db.commit()
        db.refresh(deletion_request)

        # return message
        return {
            "message": "Deletion Request Sent"
        }
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
    
# Courier account deletion     
@router.delete('/{order_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_Courier(
    courier_id: int, 
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    # Check if current_user is admin or laundromat
    if current_user.user_type in ["admin"]:
        courier = db.query(Courier).get(courier_id)
        if not courier:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Courier with id: {courier_id} does not exist")
        
        # Delete the order
        db.delete(courier)
        
        # Update the corresponding deletion request
        deletion_request = db.query(CourierDeletionRequest).filter(
            CourierDeletionRequest.courier_id == courier_id,
            CourierDeletionRequest.processed == False
        ).first()
        
        if deletion_request:
            deletion_request.processed = True
        
        db.commit()
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")
    
