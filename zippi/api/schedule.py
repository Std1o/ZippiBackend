from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ..model.auth import User
from ..model.schedule import TimeSlot, TimeSlotResponse
from ..service.auth import get_current_user
from ..service.schedule import ScheduleService

router = APIRouter(prefix='/schedule', tags=['Расписание'])


@router.post('/slot', response_model=TimeSlotResponse)
def add_time_slot(
    slot: TimeSlot,
    user: User = Depends(get_current_user),
    service: ScheduleService = Depends()
):
    """Добавить слот работы"""
    if not user.is_courier:
        raise HTTPException(status_code=403, detail="Только для курьеров")
    return service.add_time_slot(user.id, slot)


@router.delete('/slot/{slot_id}')
def delete_time_slot(
    slot_id: int,
    user: User = Depends(get_current_user),
    service: ScheduleService = Depends()
):
    """Удалить слот работы"""
    if not user.is_courier:
        raise HTTPException(status_code=403, detail="Только для курьеров")
    service.delete_time_slot(slot_id, user.id)
    return {"success": True}


@router.get('/slots', response_model=List[TimeSlotResponse])
def get_time_slots(
    user: User = Depends(get_current_user),
    service: ScheduleService = Depends()
):
    """Получить все слоты курьера"""
    if not user.is_courier:
        raise HTTPException(status_code=403, detail="Только для курьеров")
    return service.get_time_slots(user.id)