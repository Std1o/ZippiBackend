from pydantic import BaseModel
from datetime import datetime
from typing import List

class TimeSlot(BaseModel):
    start_time: datetime
    end_time: datetime

class TimeSlotResponse(BaseModel):
    id: int
    courier_id: int
    start_time: datetime
    end_time: datetime