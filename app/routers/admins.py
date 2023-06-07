#This API was developed by Alex Mutonga
from typing import List
from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from app import models, oauth2
from app import schemas, utils
from app.database import get_db

router=APIRouter(
    prefix="/admin",
    tags=['admin']
)


#create a new admin
@router.post("/", status_code=status.HTTP_201_CREATED, response_model= schemas.AdminOut)
def create_admin(admin: schemas.AdminCreate,
                #  current_user: schemas.TokenData = Depends(oauth2.get_current_user),
                 db: Session = Depends(get_db)):

        # Check if the current user is an admin or laundromat
    # if current_user.user_type not in ["admin", "laundromat"]:
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")


      # Check if email already exists
    if db.query(models.Admin).filter(models.Admin.email == admin.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    # Check if phone number already exists
    if db.query(models.Admin).filter(models.Admin.phone_number == admin.phone_number).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone number already exists")
    

    #hash the password - courierts.password
    hashed_password = utils.hash(admin.password)
    admin.password = hashed_password

    new_admin = models.Admin(**admin.dict())
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    # Convert new_couriert object to dictionary
    new_admin_dict = new_admin.__dict__

    # Remove the "_sa_instance_state" key from the dictionary
    new_admin_dict.pop("_sa_instance_state", None)

    return new_admin_dict

#fetch all admins
@router.get("/", response_model=List[schemas.AdminOut], status_code=status.HTTP_200_OK)
def get_admin(current_user: schemas.TokenData = Depends (oauth2.get_current_user), db: Session = Depends(get_db)
    ) -> List[schemas.AdminOut]:
    # check if logged in account is admin
    if current_user.user_type not in ["admin"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")
    admin = db.query(models.Admin).all()
    return [admin.__dict__ for admin in admin]

#get admin by id
@router.get('/{admin_id}', response_model=schemas.AdminOut, status_code=status.HTTP_200_OK)
def get_admin(admin_id: int, current_user: schemas.TokenData = Depends (oauth2.get_current_user),
              db: Session = Depends(get_db)) -> schemas.AdminOut:
    #check whether current_user is Admin
    if current_user.user_type not in ["admin"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")
    admin = db.query(models.Admin).filter(models.Admin.admin_id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"admin with id: {admin_id} does not exist")
    return admin

#update admin
@router.put('/{admin_id}', response_model=schemas.AdminOut, status_code=status.HTTP_200_OK)
def update_admin(admin_id: int, admin: schemas.AdminCreate, current_user: schemas.TokenData = Depends (oauth2.get_current_user),
                 db: Session = Depends(get_db)) -> schemas.AdminOut:
    #check whether current_user is Admin
    if current_user.user_type not in ["admin"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")
    current_admin = db.query(models.Admin).filter(models.Admin.admin_id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"admin with id: {admin_id} does not exist")
    
    # Update the courier fields
    for field, value in admin.dict(exclude_unset=True).items():
            # Check if the field is 'password'
            if field == 'password' and value:
                hashed_password = utils.hash(admin.password)  # Hash the new password
                setattr(current_admin, field, hashed_password)
            else:
                setattr(current_admin, field, value)
                db.add(current_admin)
                db.commit()
                #create a response model
                return current_admin

#delete admin
@router.delete('/{admin_id}', response_model=schemas.AdminOut, status_code=status.HTTP_200_OK)
def delete_admin(admin_id: int, current_user: schemas.TokenData = Depends (oauth2.get_current_user),
                 db: Session = Depends(get_db)) -> schemas.AdminOut:
    #check whether current_user is Admin
    if current_user.user_type not in ["admin"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")
    
    # Fetch the admin from the database and check if admin exists
    admin = db.query(models.Admin).filter(models.Admin.admin_id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"admin with id: {admin_id} does not exist")
    
    # Delete the admin from the database
    db.delete(admin)
    db.commit()
    return admin
