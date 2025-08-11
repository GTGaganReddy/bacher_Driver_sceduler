from fastapi import APIRouter, Depends, HTTPException
from datetime import date, timedelta
from services.database import DatabaseService
from services.optimizer import SchedulingOptimizer
from services.google_sheets import GoogleSheetsService
from schemas.models import WeekUpdate, SuccessResponse, GoogleSheetsPayload
from api.dependencies import get_database_service, get_scheduling_optimizer, get_google_sheets_service

router = APIRouter()

@router.post("/schedule/optimize", response_model=SuccessResponse)
async def optimize_schedule(
    week_data: WeekUpdate,
    db_service: DatabaseService = Depends(get_database_service),
    optimizer: SchedulingOptimizer = Depends(get_scheduling_optimizer)
):
    """Optimize driver-route assignments for a week"""
    try:
        week_start = week_data.week_start
        week_end = week_start + timedelta(days=6)
        
        # Get drivers, routes, and availability for the week
        drivers = await db_service.get_drivers()
        routes = await db_service.get_routes_by_date_range(week_start, week_end)
        availability = await db_service.get_availability_by_date_range(week_start, week_end)
        
        # Run optimization
        assignments = optimizer.optimize_assignments(drivers, routes, availability, week_start)
        
        # Save assignments to database
        await db_service.save_assignments(week_start, assignments)
        
        return SuccessResponse(
            status="success",
            message="Schedule optimized successfully",
            data={"assignments": assignments}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to optimize schedule: {str(e)}")

@router.get("/schedule/{week_start}", response_model=SuccessResponse)
async def get_schedule(
    week_start: date,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Get schedule for a specific week"""
    try:
        assignments = await db_service.get_assignments(week_start)
        if assignments:
            return SuccessResponse(
                status="success",
                message="Schedule retrieved successfully",
                data={"assignments": assignments}
            )
        else:
            return SuccessResponse(
                status="success",
                message="No schedule found for this week",
                data={"assignments": []}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve schedule: {str(e)}")

@router.post("/schedule/export", response_model=SuccessResponse)
async def export_to_google_sheets(
    payload: GoogleSheetsPayload,
    sheets_service: GoogleSheetsService = Depends(get_google_sheets_service)
):
    """Export schedule to Google Sheets"""
    try:
        result = await sheets_service.update_sheet(payload.drivers)
        return SuccessResponse(
            status="success",
            message="Schedule exported to Google Sheets successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export to Google Sheets: {str(e)}")
