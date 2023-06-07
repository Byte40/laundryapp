#This API was developed by Alex Mutonga
from typing import List
from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from app import models, oauth2
from app import schemas, utils
from app.database import get_db

router=APIRouter(
    prefix="/laundromat",
    tags=['laundromat']
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model= schemas.LaundromatOut)
def create_laundromat(laundromat: schemas.LaundromatCreate, db: Session = Depends(get_db)):


      # Check if email already exists
    if db.query(models.Laundromat).filter(models.Laundromat.email == laundromat.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    # Check if phone number already exists
    if db.query(models.Laundromat).filter(models.Laundromat.phone_number == laundromat.phone_number).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone number already exists")

    #hash the password - laundromats.password
    hashed_password = utils.hash(laundromat.password)
    laundromat.password = hashed_password

    new_laundromat = models.Laundromat(**laundromat.dict())
    db.add(new_laundromat)
    db.commit()
    db.refresh(new_laundromat)

    # Convert new_laundromat object to dictionary
    new_laundromat_dict = new_laundromat.__dict__

    # Remove the "_sa_instance_state" key from the dictionary
    new_laundromat_dict.pop("_sa_instance_state", None)

    return new_laundromat_dict

@router.get("/", response_model=List[schemas.LaundromatOut], status_code=status.HTTP_200_OK)
def get_laundromats(current_user: schemas.TokenData = Depends(oauth2.get_current_user),
                    db: Session = Depends(get_db)
                    ) -> List[schemas.LaundromatOut]:
    
    # Laundroromat fetching their own info
    if current_user.user_type == "laundromat":
        if current_user.laundromat_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized")
        #check if current_user_id and id requested match
        laundromat_id = int (current_user.laundromat_id)
        laundromat = db.query(models.Laundromat).filter(models.Laundromat.laundromat_id == laundromat_id).first()
        if laundromat is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Laundromat not found")
        return [laundromat]

    # Check whether current user is admin
    if current_user.user_type in ["admin"]:
        #fetch all Laundromats
        laundromats = db.query(models.Laundromat).all()
        return [laundromats.__dict__ for laundromats in laundromats]
    
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized")

# Get Laundromat by id
@router.get('/{laundromat_id}', response_model=schemas.LaundromatOut, status_code=status.HTTP_200_OK)
def get_laundromat(laundromat_id: int, 
                   current_user: schemas.TokenData = Depends(oauth2.get_current_user), 
                   db: Session = Depends(get_db)
                   ) -> schemas.LaundromatOut:
    # Check user is admin
    if current_user.user_type in ["admin"]:
    # Check if laundromat exists
        laundromat = db.query(models.Laundromat).filter(models.Laundromat.laundromat_id == laundromat_id).first()

        if not laundromat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"laundromat with id: {laundromat_id} does not exist")
        return laundromat
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized")

# Update Laundromat by id
@router.put('/{laundromat_id}', response_model=schemas.LaundromatOut, status_code=status.HTTP_200_OK)
def update_laundromat(laundromat_id: int, 
                      laundromat: schemas.LaundromatCreate, 
                      current_user: schemas.TokenData = Depends(oauth2.get_current_user), 
                      db: Session = Depends(get_db)
                      ) -> schemas.LaundromatOut:
    # Check user is laundromat
    if current_user.user_type in ["laundromat"]:
        # Check if laundromat exists
        current_laundromat = db.query(models.Laundromat).filter(models.Laundromat.laundromat_id == laundromat_id).first()
        if not current_laundromat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"laundromat with id: {laundromat_id} does not exist")
        
        # Check if the current laundromat_id matches the current_user id
        if current_laundromat.laundromat_id != current_user.laundromat_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized")
        #update the laundromat fields
        for field, value in laundromat.dict(exclude_unset=True).items():
            # Check if the field is 'password'
            if field == 'password' and value:
                hashed_password = utils.hash(laundromat.password)  # Hash the new password
                setattr(current_laundromat, field, hashed_password)
            else:
                setattr(current_laundromat, field, value)

            db.commit()
            db.refresh(current_laundromat)

            # Create Response Model
            return current_laundromat.__dict__
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized")

# Delete Laundromat Accounts
@router.delete("/{laundromat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_laundromat(
                        laundromat_id: int, 
                        db: Session = Depends(get_db), 
                        current_user: schemas.TokenData = Depends(oauth2.get_current_user)):
    # Check user is laundromat
    if current_user.user_type in ["laundromat"]:
        current_laundromat = db.query(models.Laundromat).filter(models.Laundromat.laundromat_id == laundromat_id).first()
        if not current_laundromat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Laundromat with id: {laundromat_id} does not exist")
        # Check if the current laundromat_id matches the current_user id
        if current_laundromat.laundromat_id != current_user.laundromat_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized")
        db.delete(current_laundromat)
        db.commit()
        return  
    return Response(status_code=status.HTTP_204_NO_CONTENT)


    #delete post
    #find the index in the arry that has the reqiured id 
    #my_posts.pop(index)
    # cursor.execute("""DELETE FROM posts WHERE id =%s RETURNING * """, (str(id),))
    # deleted_post = cursor.fetchone()
    # conn.commit()
