from enum import Enum

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