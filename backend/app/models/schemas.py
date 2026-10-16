from pydantic import BaseModel
from typing import Optional

class County(BaseModel):
    id: int
    name: str
    code: str
    capital: str
    population: Optional[int] = None
    area_km2: Optional[float] = None

class Facility(BaseModel):
    id: int
    name: str
    type: str
    county: str
    latitude: float
    longitude: float
