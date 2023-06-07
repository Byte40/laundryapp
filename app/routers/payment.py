import stripe
import os
from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from app import schemas, oauth2
from app import models
from app.database import get_db
from app.models import Order, Payment, Customer, PaymentDeletionRequest
from datetime import datetime
from typing import List
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/payments",
    tags=['payments']
)

# Set up Stripe API keys

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.PaymentOut)
def create_payment(
    payment: schemas.PaymentCreate,
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    # Check if the current user is a customer
    if current_user.user_type != "customer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")

    # Fetch the customer from the database using the authenticated user's ID
    customer = db.query(Customer).get(current_user.id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    # Create the payment with the associated customer_id
    new_payment = Payment(
        amount=payment.amount,
        payment_date=datetime.utcnow(),
        customer_id=customer.customer_id
    )

    # Charge the payment using the Stripe API
    try:
        charge = stripe.PaymentIntent.create(
            amount=int(payment.amount * 100),  # Stripe expects the amount in cents
            currency="usd",  # Replace with your desired currency
            description="Payment for laundry service",  # Replace with your payment description
            customer=customer.stripe_customer_id,  # Replace with the customer's Stripe Customer ID
            api_key=os.getenv("STRIPE_API_KEY")  # Use the environment variable for the API key
        )

        # Update the payment status and stripe_payment_id
        new_payment.status = charge.status
        new_payment.stripe_payment_id = charge.id
    except stripe.error.StripeError as e:
        # Handle Stripe API errors
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    # Fetch the latest order of the customer
    latest_order = db.query(Order).filter_by(customer_id=customer.customer_id).order_by(Order.created_at.desc()).first()

    if latest_order:
        # Update the payment_id in the latest order
        latest_order.payment_id = new_payment.id

        db.commit()

    return new_payment



@router.get("/", response_model=List[schemas.PaymentOut])
def get_payments(
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
) -> List[schemas.PaymentOut]:
    # Check if the current user is a customer and return all payments with the current user id
    if current_user.user_type == "customer":
        payments = db.query(Payment).filter_by(customer_id=current_user.id).all()

    # Check if the current user is an admin or a laundromat and return all payments
    elif current_user.user_type in ["admin", "laundromat"]:
        payments = db.query(Payment).all()
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")

    # Retrieve payment details from Stripe API and update payment status
    for payment in payments:
        if payment.stripe_payment_id:
            try:
                stripe_payment = stripe.PaymentIntent.retrieve(payment.stripe_payment_id)
                payment.status = stripe_payment.status
            except stripe.error.StripeError as e:
                # Handle Stripe API errors
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return payments


@router.get('/{payment_id}', response_model=schemas.PaymentOut)
def get_payment(
    payment_id: int,
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
) -> schemas.PaymentOut:
    # Check if the current user is a customer
    if current_user.user_type == "customer":
        # Fetch the payment from the database and check if it exists and belongs to the customer
        payment = db.query(Payment).filter(Payment.id == payment_id, Payment.customer_id == current_user.id).first()
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Payment with id: {payment_id} does not exist")
    elif current_user.user_type in ["admin", "laundromat"]:
        # Fetch the payment from the database and check if it exists
        payment = db.query(Payment).get(payment_id)
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Payment with id: {payment_id} does not exist")
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")

    # Retrieve payment details from Stripe API and update payment status
    if payment.stripe_payment_id:
        try:
            stripe_payment = stripe.PaymentIntent.retrieve(payment.stripe_payment_id)
            payment.status = stripe_payment.status
        except stripe.error.StripeError as e:
            # Handle Stripe API errors
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return payment


@router.put('/{payment_id}', response_model=schemas.PaymentUpdate)
def update_payment(
    payment_id: int,
    payment: schemas.PaymentUpdate,
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    # Check if the current user is a customer
    if current_user.user_type != "customer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")

    # Fetch the payment from the database and check if it exists
    current_payment = db.query(Payment).filter(Payment.id == payment_id, Payment.customer_id == current_user.id).first()
    if not current_payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Payment with id: {payment_id} not found")

    # Update the payment fields
    for field, value in payment.dict(exclude_unset=True).items():
        setattr(current_payment, field, value)

    # Commit the changes to the database
    db.commit()
    db.refresh(current_payment)

    return current_payment


@router.delete('/{payment_id}/request', status_code=status.HTTP_200_OK)
def request_payment_deletion(
    payment_id: int,
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    # Check if the current user is a customer
    if current_user.user_type == "customer":
        # Fetch the payment from the database and check if it exists and belongs to the customer
        payment = db.query(Payment).filter(Payment.id == payment_id, Payment.customer_id == current_user.id).first()
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unauthorized access to Payment with id: {payment_id}")

        # Check if the deletion request already exists for this payment and customer
        existing_request = db.query(PaymentDeletionRequest).filter(
            PaymentDeletionRequest.payment_id == payment_id,
            PaymentDeletionRequest.customer_id == current_user.id
        ).first()
        if existing_request:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deletion request already exists")

        # Create a new deletion request
        deletion_request = PaymentDeletionRequest(
            payment_id=payment_id,
            customer_id=current_user.id
        )
        db.add(deletion_request)
        db.commit()
        db.refresh(deletion_request)

        return {"message": f"Request to cancel payment with id: {payment_id} sent successfully"}

    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Only customers can request payment deletion")


@router.delete('/{payment_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(
    payment_id: int,
    current_user: schemas.TokenData = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    # Check if the current user is an admin or laundromat
    if current_user.user_type in ["admin", "laundromat"]:
        payment = db.query(models.Payment).get(payment_id)
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Payment with id: {payment_id} does not exist")

        # Delete the payment
        db.delete(payment)

        # Update the corresponding deletion request
        deletion_request = db.query(models.PaymentDeletionRequest).filter(
            models.PaymentDeletionRequest.payment_id == payment_id,
            models.PaymentDeletionRequest.processed == False
        ).first()

        if deletion_request:
            deletion_request.processed = True

        db.commit()

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")
