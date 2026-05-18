from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from zippi.model.auth import UserCreate, PrivateUser, User, PassportDataUpdate, PassportDataResponse, Transport, \
    CourierSimpleResponse
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

@router.post('/passport', response_model=PassportDataResponse)
def save_passport_data(
    passport_data: PassportDataUpdate,
    user: User = Depends(get_current_user),
    service: AuthService = Depends()
):
    """Сохранение паспортных данных текущего пользователя"""
    return service.save_passport_data(user.id, passport_data)


@router.get('/passport', response_model=Optional[PassportDataResponse])
def get_passport_data(
    user: User = Depends(get_current_user),
    service: AuthService = Depends()
):
    """Получение паспортных данных текущего пользователя"""
    return service.get_passport_data(user.id)

@router.post('/transport')
def update_transport(
    transport: Transport,
    user: User = Depends(get_current_user),
    service: AuthService = Depends()
):
    """Установить транспорт курьера"""
    return service.update_transport(user.id, transport)

@router.get('/update-phone')
def update_phone(user_id: int, phone: str, service: AuthService = Depends()):
    return service.update_phone(user_id, phone)

@router.get('/couriers', response_model=List[CourierSimpleResponse])
def get_couriers(
    service: AuthService = Depends(),
):
    """Получить список всех курьеров"""
    return service.get_all_couriers()