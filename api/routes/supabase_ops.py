from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import date
from services.supabase_client import SupabaseService
from schemas.models import SuccessResponse
from pydantic import BaseModel

router = APIRouter()

# Pydantic models for Supabase operations
class AvailabilityUpdate(BaseModel):
    driver_id: int
    date: str
    available: Optional[bool] = None
    available_hours: Optional[int] = None
    max_routes: Optional[int] = None
    shift_preference: Optional[str] = None
    notes: Optional[str] = None

class BatchAvailabilityUpdate(BaseModel):
    updates: List[AvailabilityUpdate]

class RouteData(BaseModel):
    date: str
    route_name: str
    details: Dict[str, Any]
    day_of_week: Optional[str] = None

class BatchRouteData(BaseModel):
    routes: List[RouteData]

class EmergencyRoute(BaseModel):
    date: str
    route_name: str
    duration: str

class DriverUnavailable(BaseModel):
    driver_id: int
    date: str
    reason: str

def get_supabase_service() -> SupabaseService:
    """Dependency to get Supabase service instance"""
    return SupabaseService()

# Driver Availability Management Endpoints
@router.put("/supabase/driver-availability", response_model=SuccessResponse)
async def update_driver_availability_supabase(
    availability: AvailabilityUpdate,
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
    """Update a single driver's availability using Supabase client"""
    try:
        update_data = availability.dict(exclude={'driver_id', 'date'}, exclude_none=True)
        result = await supabase_service.update_driver_availability(
            availability.driver_id, 
            availability.date, 
            update_data
        )
        return SuccessResponse(
            status="success",
            message="Driver availability updated via Supabase",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update availability: {str(e)}")

@router.put("/supabase/driver-availability/batch", response_model=SuccessResponse)
async def batch_update_driver_availability_supabase(
    batch_data: BatchAvailabilityUpdate,
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
    """Update multiple drivers' availability using Supabase client"""
    try:
        updates = [update.dict() for update in batch_data.updates]
        result = await supabase_service.batch_update_driver_availability(updates)
        return SuccessResponse(
            status="success",
            message=f"Updated {len(updates)} driver availability records via Supabase",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to batch update availability: {str(e)}")

@router.post("/supabase/driver-availability", response_model=SuccessResponse)
async def create_availability_record_supabase(
    availability: AvailabilityUpdate,
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
    """Create new availability record using Supabase client"""
    try:
        availability_data = availability.dict(exclude_none=True)
        result = await supabase_service.create_availability_record(availability_data)
        return SuccessResponse(
            status="success",
            message="Availability record created via Supabase",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create availability: {str(e)}")

@router.get("/supabase/driver-availability", response_model=SuccessResponse)
async def get_driver_availability_supabase(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
    """Get driver availability using Supabase client"""
    try:
        result = await supabase_service.get_driver_availability(date, start_date, end_date)
        return SuccessResponse(
            status="success",
            message="Driver availability retrieved via Supabase",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get availability: {str(e)}")

@router.delete("/supabase/driver-availability", response_model=SuccessResponse)
async def delete_availability_record_supabase(
    driver_id: int,
    date: str,
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
    """Delete availability record using Supabase client"""
    try:
        result = await supabase_service.delete_availability_record(driver_id, date)
        return SuccessResponse(
            status="success",
            message="Availability record deleted via Supabase",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete availability: {str(e)}")

# Route Management Endpoints
@router.post("/supabase/routes", response_model=SuccessResponse)
async def add_route_supabase(
    route: RouteData,
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
    """Add new route using Supabase client"""
    try:
        route_data = route.dict()
        result = await supabase_service.add_new_route(route_data)
        return SuccessResponse(
            status="success",
            message="Route added via Supabase",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add route: {str(e)}")

@router.post("/supabase/routes/batch", response_model=SuccessResponse)
async def batch_add_routes_supabase(
    batch_data: BatchRouteData,
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
    """Add multiple routes using Supabase client"""
    try:
        routes = [route.dict() for route in batch_data.routes]
        result = await supabase_service.batch_add_routes(routes)
        return SuccessResponse(
            status="success",
            message=f"Added {len(routes)} routes via Supabase",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to batch add routes: {str(e)}")

@router.put("/supabase/routes/{route_id}", response_model=SuccessResponse)
async def update_route_supabase(
    route_id: int,
    route: RouteData,
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
    """Update route using Supabase client"""
    try:
        route_data = route.dict()
        result = await supabase_service.update_route(route_id, route_data)
        return SuccessResponse(
            status="success",
            message="Route updated via Supabase",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update route: {str(e)}")

@router.delete("/supabase/routes", response_model=SuccessResponse)
async def delete_route_supabase(
    route_id: Optional[int] = None,
    date: Optional[str] = None,
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
    """Delete route(s) using Supabase client"""
    try:
        result = await supabase_service.delete_route(route_id, date)
        return SuccessResponse(
            status="success",
            message="Route(s) deleted via Supabase",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete route: {str(e)}")

@router.get("/supabase/routes", response_model=SuccessResponse)
async def get_routes_supabase(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
    """Get routes using Supabase client"""
    try:
        result = await supabase_service.get_routes(date, start_date, end_date)
        return SuccessResponse(
            status="success",
            message="Routes retrieved via Supabase",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get routes: {str(e)}")

# Advanced Query Endpoints
@router.get("/supabase/scheduling/available-drivers", response_model=SuccessResponse)
async def get_available_drivers_for_scheduling_supabase(
    date: str,
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
    """Get available drivers for scheduling using Supabase client"""
    try:
        result = await supabase_service.get_available_drivers_for_scheduling(date)
        return SuccessResponse(
            status="success",
            message="Available drivers retrieved via Supabase",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available drivers: {str(e)}")

@router.get("/supabase/scheduling/compatibility", response_model=SuccessResponse)
async def get_route_driver_compatibility_supabase(
    date: str,
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
    """Get route-driver compatibility data using Supabase client"""
    try:
        result = await supabase_service.get_route_driver_compatibility(date)
        return SuccessResponse(
            status="success",
            message="Route-driver compatibility data retrieved via Supabase",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get compatibility data: {str(e)}")

# Utility Endpoints
@router.put("/supabase/drivers/mark-unavailable", response_model=SuccessResponse)
async def mark_driver_unavailable_supabase(
    unavailable_data: DriverUnavailable,
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
    """Mark driver unavailable using Supabase client"""
    try:
        result = await supabase_service.mark_driver_unavailable(
            unavailable_data.driver_id,
            unavailable_data.date,
            unavailable_data.reason
        )
        return SuccessResponse(
            status="success",
            message="Driver marked unavailable via Supabase",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark driver unavailable: {str(e)}")

@router.post("/supabase/routes/emergency", response_model=SuccessResponse)
async def add_emergency_route_supabase(
    emergency_route: EmergencyRoute,
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
    """Add emergency route using Supabase client"""
    try:
        result = await supabase_service.add_emergency_route(
            emergency_route.date,
            emergency_route.route_name,
            emergency_route.duration
        )
        return SuccessResponse(
            status="success",
            message="Emergency route added via Supabase",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add emergency route: {str(e)}")