from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional, Dict, Any

# Driver Models
class Driver(BaseModel):
    driver_id: int
    name: str
    created_at: Optional[datetime] = None

class DriverCreate(BaseModel):
    name: str

# Availability Models
class DriverAvailabilityUpdate(BaseModel):
    driver_id: int
    date: date
    available: bool

class DriverAvailability(BaseModel):
    id: int
    driver_id: int
    date: date
    available: bool
    name: Optional[str] = None

# Route Models
class RouteCreate(BaseModel):
    date: date
    route_name: str
    day_of_week: Optional[str] = None
    details: Optional[Dict[str, Any]] = {}

class RouteUpdate(BaseModel):
    route_id: Optional[int] = None
    date: date
    route_name: str
    day_of_week: Optional[str] = None
    details: Optional[Dict[str, Any]] = {}

class Route(BaseModel):
    route_id: int
    date: date
    route_name: str
    day_of_week: Optional[str] = None
    details: Optional[Any] = {}  # Support both dict and string from JSONB

# Scheduling Models
class WeekUpdate(BaseModel):
    week_start: date

class Assignment(BaseModel):
    driver: str
    route: str
    hour: str
    remaining_hour: str
    date: str
    status: str = "update"

class GoogleSheetsPayload(BaseModel):
    drivers: List[Assignment]

# Response Models
class SuccessResponse(BaseModel):
    status: str = "success"
    message: str
    data: Optional[Any] = None
