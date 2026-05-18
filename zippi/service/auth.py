import sys
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.hash import bcrypt
from pydantic import ValidationError
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from ..database import get_session
from ..model.auth import User, UserCreate, PrivateUser, PassportDataResponse, PassportDataUpdate, Transport
from ..settings import settings
from jose import jwt, JWTError
from .. import tables

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/sign-in')

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    return AuthService.validate_token(token)


class AuthService:
    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.verify(plain_password, hashed_password)

    @classmethod
    def hash_password(cls, password: str) -> str:
        return bcrypt.hash(password)

    @classmethod
    def validate_token(cls, token: str) -> User:
        exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={
                'WWW-Authenticate': 'Bearer'
            }
        )
        try:
            payload = jwt.decode(token, settings.jwt_sercret, algorithms=[settings.jwt_algorithm])
        except JWTError:
            raise exception from None

        user_data = payload.get('user')

        try:
            user = User.parse_obj(user_data)
        except ValidationError:
            raise exception from None
        return user

    @classmethod
    def create_token(cls, user: tables.User) -> str:

        try:
            user_data = User.from_orm(user)
            now = datetime.utcnow()

            # Получаем словарь
            user_dict = user_data.dict()

            payload = {
                'iat': now,
                'nbf': now,
                'exp': now + timedelta(seconds=settings.jwt_expiration),
                'sub': str(user_data.id),
                'user': user_dict
            }
            # Проверяем сериализацию
            import json
            try:
                test_json = json.dumps(payload)
            except Exception as e:
                # Найдем проблемное поле
                for key, value in payload.items():
                    try:
                        json.dumps({key: value})
                    except Exception as e:

                        if key == 'user':
                            for subkey, subvalue in value.items():
                                try:
                                    json.dumps({subkey: subvalue})
                                except Exception as e:
                                    raise
            # Кодируем токен
            token = jwt.encode(payload, settings.jwt_sercret, algorithm=settings.jwt_algorithm)

            return token

        except Exception as e:
            raise

    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def get_user_by_phone(self, phone: str) -> tables.User:
        statement = select(tables.User).filter_by(phone=phone)
        return self.session.execute(statement).scalars().first()

    def get_user(self, user_id: int) -> tables.User:
        statement = select(tables.User).filter_by(id=user_id)
        return self.session.execute(statement).scalars().first()

    def reg(self, user_data: UserCreate) -> PrivateUser:
        if self.get_user_by_phone(user_data.phone):
            raise HTTPException(status_code=418, detail="User with this phone already exists")
        user = tables.User(
            phone=user_data.phone,
            username=user_data.username,
            password_hash=self.hash_password(user_data.password))
        self.session.add(user)
        self.session.commit()
        token = self.create_token(user)
        created_user = self.session.query(tables.User).filter_by(phone=user.phone).first()
        return PrivateUser(phone=created_user.phone,
                           username=created_user.username,
                           id=created_user.id,
                           access_token=token)

    # Настройка логирования

    def auth(self, phone: str, password: str) -> PrivateUser:
        exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={
                'WWW-Authenticate': 'Bearer'
            }
        )
        user = self.session.query(tables.User).filter_by(phone=phone).first()
        if not user:
            raise exception
        if not self.verify_password(password, user.password_hash):
            raise exception
        token = self.create_token(user)
        user_dict = {
            'phone': user.phone,
            'username': user.username,
            'id': user.id,
            'access_token': token,
            'token_type': 'bearer',
            'transport': user.transport
        }
        try:
            private_user = PrivateUser(**user_dict)
            return private_user
        except Exception as e:
            raise

    def get_couriers_with_stats(self) -> List[Dict[str, Any]]:
        """
        Получить список курьеров с количеством завершенных заказов и отработанных часов за все время.
        """
        couriers = self.session.query(tables.User).filter(
            tables.User.is_courier == True
        ).all()

        results = []

        for courier in couriers:
            # Количество завершенных (доставленных) заказов
            completed_orders_count = self.session.query(
                func.count(tables.Order.id)
            ).filter(
                tables.Order.courier_id == courier.id,
                tables.Order.status == 'delivered'
            ).scalar() or 0

            # Отработанные часы из смен
            shifts = self.session.query(tables.Shift).filter(
                tables.Shift.courier_id == courier.id
            ).all()

            total_hours = 0.0
            for shift in shifts:
                if shift.duration_hours:
                    total_hours += shift.duration_hours
                elif shift.end_time:
                    duration = (shift.end_time - shift.start_time).total_seconds() / 3600
                    total_hours += duration

            results.append({
                'courier_id': courier.id,
                'phone': courier.phone,
                'username': courier.username,
                'completed_orders': completed_orders_count,
                'total_hours_worked': round(total_hours, 2)
            })

        return results

    def set_courier(self, user_id: int):
        user = self.get_user(user_id)
        user.is_courier = True
        self.session.commit()
        self.session.refresh(user)
        return {"success": True}

    def save_passport_data(self, user_id: int, passport_data: PassportDataUpdate) -> PassportDataResponse:
        """Сохранение паспортных данных пользователя"""
        user = self.session.query(tables.User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Сохраняем данные
        user.full_name = passport_data.full_name
        user.passport_series = passport_data.passport_series
        user.passport_number = passport_data.passport_number
        user.passport_issued_by = passport_data.passport_issued_by
        user.passport_issued_date = passport_data.passport_issued_date
        user.passport_department_code = passport_data.passport_department_code

        self.session.commit()
        self.session.refresh(user)

        return PassportDataResponse(
            full_name=user.full_name,
            passport_series=user.passport_series,
            passport_number=user.passport_number,
            passport_issued_by=user.passport_issued_by,
            passport_issued_date=user.passport_issued_date,
            passport_department_code=user.passport_department_code,
        )

    def get_passport_data(self, user_id: int) -> Optional[PassportDataResponse]:
        """Получение паспортных данных пользователя"""
        user = self.session.query(tables.User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.full_name:
            return None

        return PassportDataResponse(
            full_name=user.full_name,
            passport_series=user.passport_series,
            passport_number=user.passport_number,
            passport_issued_by=user.passport_issued_by,
            passport_issued_date=user.passport_issued_date,
            passport_department_code=user.passport_department_code,
        )

    def update_transport(self, user_id: int, transport: Transport):
        """Обновление транспорта курьера"""
        user = self.session.query(tables.User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.is_courier:
            raise HTTPException(status_code=403, detail="Only couriers can set transport")

        user.transport = transport.value
        self.session.commit()

        return {'message': 'success'}