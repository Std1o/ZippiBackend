from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BaseUser(BaseModel):
    phone: str
    username: str

class UserCreate(BaseUser):
    password: str
    is_courier: bool

class User(BaseUser):
    id: int
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'

class PrivateUser(User):
    access_token: str
    token_type: str = 'bearer'

    model_config = ConfigDict(from_attributes=True)

class Transport(str, Enum):
    CAR = "car"
    ELECTRIC_BIKE = "electric_bike"
    BIKE = "bike"
    WALKING = "walking"

class PassportDataUpdate(BaseModel):
    full_name: str
    passport_series: str
    passport_number: str
    passport_issued_by: str
    passport_issued_date: date
    passport_department_code: Optional[str] = None

class PassportDataResponse(BaseModel):
    full_name: str
    passport_series: str
    passport_number: str
    passport_issued_by: str
    passport_issued_date: date
    passport_department_code: Optional[str] = None

class CourierSimpleResponse(BaseModel):
    username: Optional[str] = None
    phone: str