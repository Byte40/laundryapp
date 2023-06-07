from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Boolean, Enum, DateTime
from app.database import Base
from app.schemas import LockerSize, LockerStatus

# Customer Model
class Customer(Base):
    __tablename__ = 'customers'

    customer_id = Column(Integer, primary_key=True, nullable=False)
    stripe_customer_id = Column(String)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)

    # Define the relationship between customers and orders
    orders = relationship("Order", back_populates="customer")
    payments = relationship('Payment', back_populates='customer')
    payment_deletion_requests = relationship('PaymentDeletionRequest', back_populates='customer')
    customer_deletion_requests = relationship("CustomerDeletionRequest", back_populates="customer")
    order_deletion_requests = relationship("OrderDeletionRequest", back_populates="customer")

# Model for customer deletion request
class CustomerDeletionRequest(Base):
    __tablename__ = 'customer_deletion_requests'

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id'))
    processed = Column(Boolean, default=False)

    # Define the relationship to Customer (not Courier)
    customer = relationship("Customer", back_populates="customer_deletion_requests")

#lockers model
class Locker(Base):
    __tablename__ = 'lockers'

    locker_id = Column(Integer, primary_key=True, nullable=False, index=True)
    locker_number = Column(String(50), unique=True, index=True)
    location = Column(String(255))
    status = Column(Enum(LockerStatus), default=LockerStatus.AVAILABLE)
    size = Column(Enum(LockerSize))
    code = Column(String(6), nullable=True)

    orders = relationship("Order", back_populates="locker")

#laundromat model
class Laundromat(Base):
    __tablename__ = 'laundromats'

    laundromat_id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)

# Courier model
class Courier(Base):
    __tablename__ = 'couriers'

    courier_id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    vehicle_reg_no = Column(String, nullable=False, unique=True)

    deletion_requests = relationship("CourierDeletionRequest", back_populates="courier")

# Courier deletion requests
class CourierDeletionRequest(Base):
    __tablename__ = 'courier_deletion_requests'

    id = Column(Integer, primary_key=True)
    courier_id = Column(Integer, ForeignKey('couriers.courier_id'))
    processed = Column(Boolean, default=False)

    courier = relationship("Courier", back_populates="deletion_requests")

# Admin model
class Admin(Base):
    __tablename__ = 'admins'

    admin_id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)

# Model for orders
class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id'))
    services = Column(String)
    weight = Column(Float)
    payment_id = Column(Integer, ForeignKey('payments.id'))
    locker_id = Column(Integer, ForeignKey('lockers.locker_id'))
    locker_code = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    customer = relationship('Customer', back_populates='orders')
    payment = relationship('Payment', back_populates='orders')
    locker = relationship('Locker', back_populates='orders')
    order_deletion_requests = relationship("OrderDeletionRequest", back_populates="order")

# Model for order deletion request
class OrderDeletionRequest(Base):
    __tablename__ = 'order_deletion_requests'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    customer_id = Column(Integer, ForeignKey('customers.customer_id'))
    processed = Column(Boolean, default=False)

    customer = relationship('Customer', back_populates='order_deletion_requests')
    order = relationship('Order', back_populates='order_deletion_requests')

# Model for payments
class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id'))
    amount = Column(Float)
    payment_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    customer = relationship('Customer', back_populates='payments')
    orders = relationship('Order', back_populates='payment')
    payment_deletion_requests = relationship('PaymentDeletionRequest', back_populates='payment')

# Model for payment deletion request
class PaymentDeletionRequest(Base):
    __tablename__ = 'payment_deletion_requests'

    id = Column(Integer, primary_key=True)
    payment_id = Column(Integer, ForeignKey('payments.id'))
    customer_id = Column(Integer, ForeignKey('customers.customer_id'))
    processed = Column(Boolean, default=False)

    customer = relationship('Customer', back_populates='payment_deletion_requests')
    payment = relationship('Payment', back_populates='payment_deletion_requests')



