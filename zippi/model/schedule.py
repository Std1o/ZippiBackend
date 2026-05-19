from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import List


class TimeSlot(BaseModel):
    start_time: str  # формат "dd.MM.yyyy HH:mm"
    end_time: str  # формат "dd.MM.yyyy HH:mm"

    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_datetime(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%d.%m.%Y %H:%M")
        except ValueError:
            raise ValueError("Неверный формат даты. Используйте dd.MM.yyyy HH:mm")
        return v


class TimeSlotResponse(BaseModel):
    id: int
    courier_id: int
    start_time: str
    end_time: str