#This API was developed by Alex Mutonga
from typing import List, Union
from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from app import models, oauth2
from app import schemas, utils
from app.database import get_db

router=APIRouter(
    prefix="/customers",
    tags=['customers']
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.CustomerOut)
async def create_customer(
    customer: schemas.CustomerCreate,
    db: Session = Depends(get_db),
):

    # Check if email already exists
    if db.query(models.Customer).filter(models.Customer.email == customer.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    # Check if phone number already exists
    if db.query(models.Customer).filter(models.Customer.phone_number == customer.phone_number).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone number already exists")

    # hash the password - customer.password
    hashed_password = utils.hash(customer.password)
    customer.password = hashed_password

    new_customer = models.Customer(**customer.dict())
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)

    # Convert new_customer object to dictionary
    new_customer_dict = new_customer.__dict__

    # Remove the "_sa_instance_state" key from the dictionary
    new_customer_dict.pop("_sa_instance_state", None)

    return new_customer_dict



@router.get("/", status_code=status.HTTP_200_OK, response_model=Union[List[schemas.CustomerOut], schemas.CustomerOut])
def get_customer(
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):

    # Customer fetching their own info
    if current_user.user_type == "customer":
        if current_user.customer_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer ID not found in token")
        # check if current_user_id and id requested match
        customer_id = int(current_user.customer_id)
        customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return customer

    # fetching all customers
    if current_user.user_type in ["admin"]:
        customers = db.query(models.Customer).all()
        return customers

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

@router.get('/{customer_id}',status_code=status.HTTP_200_OK, response_model=Union[List[schemas.CustomerOut], schemas.CustomerOut])
def get_customer(
    customer_id: int,
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    #check whether is admin or laundromat
    if current_user.user_type in ["admin", "laundromat"]:
        customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Courier with id: {customer_id} does not exist")
        return customer
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

# Updating customer Information
@router.put('/{customer_id}', status_code=status.HTTP_201_CREATED, response_model=schemas.CustomerOut)
def update_customer(
    customer_id: int,
    customer: schemas.CustomerUpdate,
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
) -> schemas.CustomerOut:
    #check whether current user is a customer
    if current_user.user_type == "customer":
        current_customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
        if not current_customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Courier with id: {customer_id} does not exist")
        
        # Check if the current_customer_id matches the current_user_id
        if current_customer.customer_id != current_user.customer_id:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
        
        #update the customer fields
        for field, value in customer.dict(exclude_unset=True).items():
            #check if the field is password
            if field == 'password' and value:
                hashed_password = utils.hash(value)
                setattr(current_customer, field, hashed_password)
            else:
                setattr(current_customer, field, value)

        #commit changes to database
        db.commit()
        db.refresh(current_customer)

        return current_customer
    
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

# Account delete Request by Customer
@router.delete('/{customer_id}/request', status_code=status.HTTP_200_OK)
def Request_customer_acount_deletion(
    customer_id: int,
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db),
):
    # Check whether current_user is customer
    if current_user.user_type == "customer":
        current_customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
        if not current_customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Customer with id: {customer_id} does not exist")
        
        # Check if the current customer ID matches the user's customer ID
        if current_customer.customer_id != current_user.customer_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
        
        # Check if the Deletion Requests already exists for this customer
        deletion_request = db.query(models.models.CustomerDeletionRequest).filter(models.models.CustomerDeletionRequest.id == customer_id).first()
        if deletion_request:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deletion Request already exists")
        
        # Create a new deletion request
        deletion_request = models.models.CustomerDeletionRequest(
            customer_id=customer_id
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
    
# Customer account deletion
@router.delete('/{courier_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_customer_account(
    customer_id: int,
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db),
):
  #check whether current user is admin
  if current_user.user_type == "admin":
          raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
  
  # Fectch the courier from database and check if courier exists
  customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
  if not customer:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Courier with id: {customer_id} does not exist")
  
  db.delete(customer)
  db.commit()

# Customer Delete
@router.delete('/{customer_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: int, 
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    # Check if current_user is admin or laundromat
    if current_user.user_type in ["admin"]:
        customer = db.query(models.Customer).get(customer_id)
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Customer with id: {customer_id} does not exist")
        
        # Delete the ocustomer
        db.delete(customer)
        
        # Update the corresponding deletion request
        deletion_request = db.query(models.CustomerDeletionRequest).filter(
            models.CustomerDeletionRequest.customer_id == customer_id,
            models.CustomerDeletionRequest.processed == False
        ).first()
        
        if deletion_request:
            deletion_request.processed = True
        
        db.commit()
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")
    