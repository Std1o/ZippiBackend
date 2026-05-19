from datetime import datetime
from typing import List
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from ..database import get_session
from ..model.schedule import TimeSlot, TimeSlotResponse
from .. import tables


class ScheduleService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def add_time_slot(self, courier_id: int, slot: TimeSlot) -> TimeSlotResponse:
        """Добавить слот"""
        # Парсим даты из строки
        start_dt = datetime.strptime(slot.start_time, "%d.%m.%Y %H:%M")
        end_dt = datetime.strptime(slot.end_time, "%d.%m.%Y %H:%M")

        if start_dt >= end_dt:
            raise HTTPException(
                status_code=400,
                detail="start_time должен быть меньше end_time"
            )

        time_slot = tables.TimeSlot(
            courier_id=courier_id,
            start_time=start_dt,
            end_time=end_dt
        )
        self.session.add(time_slot)
        self.session.commit()

        return TimeSlotResponse(
            id=time_slot.id,
            courier_id=time_slot.courier_id,
            start_time=time_slot.start_time.strftime("%d.%m.%Y %H:%M"),
            end_time=time_slot.end_time.strftime("%d.%m.%Y %H:%M")
        )

    def delete_time_slot(self, slot_id: int, courier_id: int) -> None:
        """Удалить слот"""
        slot = self.session.query(tables.TimeSlot).filter(
            tables.TimeSlot.id == slot_id,
            tables.TimeSlot.courier_id == courier_id
        ).first()

        if not slot:
            raise HTTPException(status_code=404, detail="Слот не найден")

        self.session.delete(slot)
        self.session.commit()

    def get_time_slots(self, courier_id: int) -> List[TimeSlotResponse]:
        """Получить все слоты курьера"""
        slots = self.session.query(tables.TimeSlot).filter(
            tables.TimeSlot.courier_id == courier_id
        ).order_by(tables.TimeSlot.start_time.asc()).all()

        return [
            TimeSlotResponse(
                id=s.id,
                courier_id=s.courier_id,
                start_time=s.start_time.strftime("%d.%m.%Y %H:%M"),
                end_time=s.end_time.strftime("%d.%m.%Y %H:%M")
            )
            for s in slots
        ]