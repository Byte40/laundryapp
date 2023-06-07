# This API was developed by Alex Mutonga
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from enum import Enum

#schemas for customers
class CustomerCreate(BaseModel):
    name: str
    phone_number: str
    email: str
    password: str

class CustomerOut(BaseModel):
    customer_id: int
    name: str
    phone_number: Optional[str]
    email: str

    class Config:
        orm_mode = True

class CustomerUpdate(BaseModel):
    name: str
    phone_number: str
    email: str
    password: str

class CustomerLogin(BaseModel):
    email: EmailStr
    password: str

#schemas for payments
class PaymentBase(BaseModel):
    amount: float
    payment_date: datetime = Field(default_factory=datetime.utcnow)

class PaymentCreate(PaymentBase):
    class Config:
        orm_mode = True

class PaymentUpdate(PaymentBase):
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class PaymentOut(BaseModel):
    id: int
    amount: float
    payment_date: datetime
    customer_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True

#schemas for orders
class OrderBase(BaseModel):
    services: str
    weight: float

class OrderCreate(OrderBase):
    pass

class OrderUpdate(OrderBase):
    pass

class OrderOut(OrderBase):
    id: int
    # customer_id: int

    class Config:
        orm_mode = True


#schemas for laundromats
class LaundromatCreate(BaseModel):
    name: str
    phone_number: str
    email: str
    password: str

class LaundromatOut(BaseModel):
    laundromat_id: int
    name: str
    phone_number: Optional[str]
    email: str

    class Config:
        orm_mode = True

class LaundromatLogin(BaseModel):
    email: EmailStr
    password: str

#schemas for couriers
class CourierBase(BaseModel):
    name: str
    phone_number: str
    email: str
    vehicle_reg_no: str

class CourierCreate(CourierBase):
    password: str
    pass

class CourierUpdate(CourierBase):
    password: str
    pass

class CourierOut(CourierBase):
    pass
    courier_id: int

    class Config:
        orm_mode = True
        # Exclude the 'password' field from the response
        exclude = ['password']

class CourierLogin(BaseModel):
    email: EmailStr
    password: str

#schemas for administrators
class AdminCreate(BaseModel):
    name: str
    phone_number: str
    email: str
    password: str

class AdminOut(BaseModel):
    admin_id: int
    name: str
    phone_number: Optional[str]
    email: str

    class Config:
        orm_mode = True

class AdminLogin(BaseModel):
    email: EmailStr
    password: str
    
#schemas for locker system (lockers)
class LockerStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"

class LockerSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class LockerCreate(BaseModel):
    locker_number: str
    location: str
    # status: LockerStatus
    size: LockerSize

class LockerOut(BaseModel):
    locker_id: int
    locker_number: str
    location: str
    status: LockerStatus
    size: LockerSize

    class Config:
        orm_mode = True

#schemas for tokenisation
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[str] = None
    user_type: Optional[str] = None
    customer_id: Optional[int] = None
    email: Optional[str] = None
    courier_id: Optional[int] = None
    laundromat_id: Optional[int] = None
