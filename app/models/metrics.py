from pydantic import BaseModel
from typing import List

class Measurement(BaseModel):
    datetime: str
    value: float

class MetricsResponse(BaseModel):
    calendar_date: str
    measurements: List[Measurement]
