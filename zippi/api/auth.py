from typing import List, Dict, Any

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from zippi.model.auth import UserCreate, PrivateUser, User
from zippi.service.auth import AuthService, get_current_user

router = APIRouter(prefix='/auth')


@router.post('/sign-up', response_model=PrivateUser)
def sign_up(user_data: UserCreate, service: AuthService = Depends()):
    return service.reg(user_data)


@router.post('/sign-in', response_model=PrivateUser)
def sign_in(form_data: OAuth2PasswordRequestForm = Depends(), service: AuthService = Depends()):
    return service.auth(form_data.username, form_data.password)


@router.get('/user', response_model=User)
def get_user(user: User = Depends(get_current_user)):
    return user


@router.get('/stats', response_model=List[Dict[str, Any]])
def get_couriers_stats(service: AuthService = Depends()):
    """
    Получить список курьеров с количеством заказов и отработанных часов.
    """
    return service.get_couriers_with_stats()

@router.get('/set_courier')
def set_courier(user: User = Depends(get_current_user), service: AuthService = Depends()):
    return service.set_courier(user.id)