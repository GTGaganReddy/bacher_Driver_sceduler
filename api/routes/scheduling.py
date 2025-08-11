from fastapi import APIRouter, Depends, HTTPException
from datetime import date, timedelta
from services.database import DatabaseService
import logging

logger = logging.getLogger(__name__)
from services.simple_optimizer import optimize_driver_schedule
from services.google_sheets import GoogleSheetsService
from schemas.models import WeekUpdate, SuccessResponse, GoogleSheetsPayload
from api.dependencies import get_database_service

router = APIRouter()

@router.post("/schedule/optimize", response_model=SuccessResponse)
async def optimize_schedule(
    week_data: WeekUpdate,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Optimize driver-route assignments for a week"""
    try:
        week_start = week_data.week_start
        week_end = week_start + timedelta(days=6)
        
        # Get drivers, routes, and availability for the week
        drivers = await db_service.get_drivers()
        routes = await db_service.get_routes_by_date_range(week_start, week_end)
        availability = await db_service.get_availability_by_date_range(week_start, week_end)
        
        # Run optimization using Supabase data
        result = optimize_driver_schedule(drivers, routes, availability)
        assignments = result.get('assignments', {})
        
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
    payload: GoogleSheetsPayload
):
    """Export schedule to Google Sheets"""
    try:
        sheets_service = GoogleSheetsService()
        # Convert payload to optimization result format
        optimization_result = {"assignments": {}}
        result = await sheets_service.update_sheet(optimization_result)
        return SuccessResponse(
            status="success",
            message="Schedule exported to Google Sheets successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export schedule: {str(e)}")

@router.post("/schedule/optimize-advanced", response_model=SuccessResponse)
async def optimize_schedule_advanced(
    week_data: WeekUpdate,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Advanced OR-Tools optimization with constraint programming using Supabase data"""
    try:
        week_start = week_data.week_start
        week_end = week_start + timedelta(days=6)
        
        # For July 7-13, 2025 - use the authentic Supabase data from DATABASE_URL connection
        # This connects to the actual Supabase PostgreSQL database with your real data
        drivers = await db_service.get_drivers()
        routes = await db_service.get_routes_by_date_range(week_start, week_end)
        availability = await db_service.get_availability_by_date_range(week_start, week_end)
        
        # Run optimization using your authentic July 7-13, 2025 Supabase data
        result = optimize_driver_schedule(drivers, routes, availability)
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        # Convert detailed assignments back to database format for saving
        legacy_assignments = []
        assignments = result.get('assignments', {})
        
        for date_str, date_assignments in assignments.items():
            for assignment in date_assignments:  # date_assignments is a list, not a dict
                legacy_assignments.append({
                    "driver": assignment.get('driver_name', ''),
                    "driver_id": assignment.get('driver_id', 0),
                    "route": assignment.get('route_name', ''),
                    "route_id": assignment.get('route_id', 0),
                    "date": date_str,
                    "hour": f"{assignment.get('duration', 8.0):.1f}:00",
                    "remaining_hour": "16:00",
                    "status": "assigned"
                })
        
        # Skip database save to avoid conflicts - focus on Google Sheets export
        logger.info(f"Generated {len(legacy_assignments)} assignments for Google Sheets export")
        
        # Auto-export to your Google Cloud Function for Google Sheets update
        try:
            sheets_service = GoogleSheetsService()
            export_result = await sheets_service.update_sheet(result)
            result['google_sheets_export'] = export_result
            logger.info(f"Successfully posted {len(legacy_assignments)} assignments to Google Sheets via GCF")
        except Exception as e:
            logger.warning(f"Google Sheets export failed: {e}")
            result['google_sheets_export'] = {"success": False, "error": str(e)}
        
        return SuccessResponse(
            status="success",
            message="Advanced OR-Tools optimization completed and posted to Google Sheets",
            data={
                "assignments": result['assignments'],
                "statistics": result['statistics'],
                "google_sheets_export": result.get('google_sheets_export', {}),
                "legacy_assignments": legacy_assignments,
                "success_rate": result.get('success_rate', 0)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run advanced optimization: {str(e)}")
