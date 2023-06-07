# This API was developed by Alex Mutonga
from typing import List
from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from app import oauth2, schemas
from app.database import get_db
from app.models import Customer, Order, OrderDeletionRequest

router = APIRouter(
    prefix="/orders",
    tags=['orders']
)

# Creating a new Order
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.OrderOut)
def create_order(
    order: schemas.OrderCreate,
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    # Check if the current user is a customer
    if current_user.user_type != "customer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Only customers can create orders")
    
    # Fetch the customer ID from the database using the authenticated user's email
    customer = db.query(Customer).get(current_user.id)  # Use `get` instead of `filter`
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    new_order = Order(
        customer=customer,  # Set the customer_id
        services=order.services,
        weight=order.weight
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

# Fetch all orders
@router.get("/", response_model=List[schemas.OrderOut], status_code=status.HTTP_200_OK)
def get_orders(
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth2.get_current_user)
) -> List[schemas.OrderOut]:
    if current_user.user_type == "customer":
        # Retrieve orders for the current customer only
        orders = db.query(Order).filter(Order.customer_id == current_user.customer_id).all()
    elif current_user.user_type in ["admin", "laundromat"]:
        # Retrieve all orders for admins and laundromats
        orders = db.query(Order).all()
    else:
        # Handle other user types if needed
        orders = []

    return orders

# Get orders by id
@router.get('/{order_id}', response_model=schemas.OrderOut, status_code=status.HTTP_200_OK)
def get_order(order_id: int, 
              current_user: schemas.TokenData = Depends(oauth2.get_current_user), 
              db: Session = Depends(get_db)) -> schemas.OrderOut:
    # Check if current_user is admin or laundromat
    if current_user.user_type in ["admin", "laundromat"]:
        # Fetch order from database
        order = db.query(Order).get(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order with id: {order_id} does not exist")
        return order
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")

# Update an order
@router.put('/{order_id}', response_model=schemas.OrderOut, status_code=status.HTTP_201_CREATED)
def update_order(
                    order_id: int, 
                    order: schemas.OrderUpdate, 
                    current_user: schemas.TokenData = Depends(oauth2.get_current_user), 
                    db: Session = Depends(get_db)):
    # Check if current_user is a customer
    if current_user.user_type != "customer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Only customers can update orders")
    # Fech the oder from the database and check if it exists and if it matches the current_user id
    current_order = db.query(Order).filter(Order.id == order_id, Order.customer_id == current_user.id).first()
    if not current_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order with id: {order_id} not found")
    # update the order fields
    for field, value in order.dict(exclude_unset=True).items():
        setattr(current_order, field, value)

    db.commit()
    db.refresh(current_order)
    return current_order

# Request for deleting an order
@router.delete('/{order_id}/request', status_code=status.HTTP_200_OK)
def request_order_deletion(
    order_id: int,
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    # Check if the current user is a customer
    if current_user.user_type == "customer":
        # Fetch the Order from the database and check if it exists and belongs to the customer
        order = db.query(Order).filter(Order.id == order_id, Order.customer_id == current_user.id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unauthorized access to Order with id: {order_id}")
        
        # Check if the deletion request already exists for this Order and customer
        existing_request = db.query(OrderDeletionRequest).filter(
            OrderDeletionRequest.order_id == order_id,
            OrderDeletionRequest.customer_id == current_user.id
        ).first()
        if existing_request:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deletion request already exists")
        
        # Create a new deletion request
        deletion_request = OrderDeletionRequest(
            order_id=order_id,
            customer_id=current_user.id
        )
        db.add(deletion_request)
        db.commit()
        db.refresh(deletion_request)
        
        return {"message": f"Request to cancel order with id: {order_id} sent successfully"}
    
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Only customers can request order deletion")

@router.delete('/{order_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: int, 
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    # Check if current_user is admin or laundromat
    if current_user.user_type in ["admin", "laundromat"]:
        order = db.query(Order).get(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order with id: {order_id} does not exist")
        
        # Delete the order
        db.delete(order)
        
        # Update the corresponding deletion request
        deletion_request = db.query(OrderDeletionRequest).filter(
            OrderDeletionRequest.order_id == order_id,
            OrderDeletionRequest.processed == False
        ).first()
        
        if deletion_request:
            deletion_request.processed = True
        
        db.commit()
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unuthorized Access")



