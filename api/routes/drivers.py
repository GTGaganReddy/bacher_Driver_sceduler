from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import date
from services.database import DatabaseService
from schemas.models import Driver, DriverCreate, DriverAvailabilityUpdate, DriverAvailability, SuccessResponse
from api.dependencies import get_database_service

router = APIRouter()

@router.get("/drivers", response_model=List[Driver])
async def get_drivers(db_service: DatabaseService = Depends(get_database_service)):
    """Get all drivers"""
    try:
        drivers = await db_service.get_drivers()
        return drivers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch drivers: {str(e)}")

@router.post("/drivers", response_model=SuccessResponse)
async def create_driver(
    driver: DriverCreate,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Create a new driver"""
    try:
        driver_id = await db_service.create_driver(driver.name)
        return SuccessResponse(
            status="success",
            message="Driver created successfully",
            data={"driver_id": driver_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create driver: {str(e)}")

@router.delete("/drivers/{driver_id}", response_model=SuccessResponse)
async def delete_driver(
    driver_id: int,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Delete a driver"""
    try:
        await db_service.delete_driver(driver_id)
        return SuccessResponse(
            status="success",
            message="Driver deleted successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete driver: {str(e)}")

@router.put("/drivers/availability", response_model=SuccessResponse)
async def update_driver_availability(
    availability: DriverAvailabilityUpdate,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Update driver availability for a specific date"""
    try:
        await db_service.update_driver_availability(
            availability.driver_id,
            availability.date,
            availability.available
        )
        return SuccessResponse(
            status="success",
            message="Driver availability updated successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update availability: {str(e)}")

@router.get("/drivers/availability", response_model=List[DriverAvailability])
async def get_driver_availability(
    start_date: date,
    end_date: date,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Get driver availability for a date range"""
    try:
        availability = await db_service.get_availability_by_date_range(start_date, end_date)
        return availability
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch availability: {str(e)}")
