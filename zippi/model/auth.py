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