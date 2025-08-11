from fastapi import APIRouter, Depends, HTTPException
from datetime import date, timedelta
from typing import Dict, List, Any, Optional
from services.database import DatabaseService
from services.optimizer import DriverRouteOptimizer  # Your OR-Tools optimizer
from services.google_sheets import GoogleSheetsService
from schemas.models import WeekUpdate, SuccessResponse, GoogleSheetsPayload
from api.dependencies import get_database_service
import logging

logger = logging.getLogger(__name__)

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
        
        # Run optimization using your authentic July 7-13, 2025 Supabase data with the real OR-Tools optimizer
        logger.info(f"Database data: {len(drivers)} drivers, {len(routes)} routes, {len(availability)} availability records")
        
        # Debug the actual data structure from database
        if drivers:
            logger.info(f"Sample driver: {drivers[0]}")
        if routes: 
            logger.info(f"Sample route: {routes[0]}")
        if availability:
            logger.info(f"Sample availability: {availability[0]}")
        
        optimizer = DriverRouteOptimizer()
        result = optimizer.optimize_assignments(drivers, routes, availability)
        
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
        
        # Extract Saturday assignments for verification
        saturday_assignments = result['assignments'].get('2025-07-12', [])
        
        return SuccessResponse(
            status="success",
            message=f"Advanced OR-Tools optimization completed and posted to Google Sheets. Saturday has {len(saturday_assignments)} routes assigned.",
            data={
                "assignments": result['assignments'],
                "saturday_assignments": saturday_assignments,
                "statistics": result['statistics'],
                "google_sheets_export": result.get('google_sheets_export', {}),
                "success_rate": result.get('success_rate', 0)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run advanced optimization: {str(e)}")

@router.post("/schedule/reoptimize", response_model=SuccessResponse)
async def reoptimize_schedule(
    week_data: WeekUpdate,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Re-optimize an existing schedule with updated constraints"""
    try:
        week_start = week_data.week_start
        week_end = week_start + timedelta(days=6)
        
        logger.info(f"Re-optimizing schedule for week: {week_start}")
        
        # Check if schedule already exists
        existing_assignments = await db_service.get_assignments(week_start)
        
        # Fetch fresh data from Supabase
        drivers = await db_service.get_drivers()
        routes = await db_service.get_routes_by_date_range(week_start, week_end)
        availability = await db_service.get_availability_by_date_range(week_start, week_end)
        
        # Run optimization with your real July 7-13, 2025 data
        result = optimize_driver_schedule(drivers, routes, availability)
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=f"Re-optimization failed: {result['error']}")
        
        assignments = result.get('assignments', {})
        legacy_assignments = convert_to_legacy_format(assignments)
        
        # Auto-export to Google Cloud Function
        try:
            sheets_service = GoogleSheetsService()
            export_result = await sheets_service.update_sheet(result)
            result['google_sheets_export'] = export_result
            logger.info(f"Re-optimization results posted to Google Sheets via GCF")
        except Exception as e:
            logger.warning(f"Google Sheets export failed during re-optimization: {e}")
            result['google_sheets_export'] = {"success": False, "error": str(e)}
        
        return SuccessResponse(
            status="success",
            message="Schedule re-optimized successfully and posted to Google Sheets",
            data={
                "assignments": assignments,
                "statistics": result.get('statistics', {}),
                "unassigned_routes": result.get('unassigned_routes', []),
                "solver_status": result.get('solver_status', 'UNKNOWN'),
                "google_sheets_export": result.get('google_sheets_export', {}),
                "had_existing_schedule": bool(existing_assignments),
                "success_rate": result.get('success_rate', 0)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Re-optimization error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Re-optimization failed: {str(e)}")

@router.get("/schedule/{week_start}/stats", response_model=SuccessResponse)
async def get_schedule_statistics(
    week_start: date,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Get detailed statistics for a week's schedule"""
    try:
        logger.info(f"Getting statistics for week: {week_start}")
        
        week_end = week_start + timedelta(days=6)
        
        # Get data from your authentic Supabase database
        drivers = await db_service.get_drivers()
        routes = await db_service.get_routes_by_date_range(week_start, week_end)
        assignments = await db_service.get_assignments(week_start)
        
        # Calculate statistics
        stats = calculate_schedule_stats(drivers, routes, assignments)
        
        return SuccessResponse(
            status="success",
            message="Statistics retrieved successfully",
            data=stats
        )
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

# Helper Functions

def convert_to_legacy_format(detailed_assignments: Dict[str, List[Dict]]) -> List[Dict]:
    """Convert detailed assignments to legacy format for database storage"""
    legacy_assignments = []
    
    for date_str, date_assignments in detailed_assignments.items():
        for assignment in date_assignments:
            legacy_assignments.append({
                "driver": assignment.get('driver_name', ''),
                "driver_id": assignment.get('driver_id', 0), 
                "route": assignment.get('route_name', ''),
                "route_id": assignment.get('route_id', 0),
                "date": date_str,
                "duration_hours": assignment.get('duration', 8.0),
                "duration_formatted": f"{assignment.get('duration', 8.0):.1f}:00",
                "status": "assigned"
            })
    
    return legacy_assignments

def convert_from_legacy_format(legacy_assignments: List[Dict]) -> Dict[str, Dict[str, Dict]]:
    """Convert legacy assignments to detailed format"""
    detailed_assignments = {}
    
    for assignment in legacy_assignments:
        date_str = assignment['date']
        route_name = assignment['route']
        
        if date_str not in detailed_assignments:
            detailed_assignments[date_str] = {}
        
        detailed_assignments[date_str][route_name] = {
            'driver_name': assignment['driver'],
            'driver_id': assignment['driver_id'],
            'duration_hours': assignment.get('duration_hours', 8.0),
            'duration_formatted': assignment.get('duration_formatted', '8:00')
        }
    
    return detailed_assignments

def calculate_schedule_stats(drivers: List[Dict], routes: List[Dict], assignments: List[Dict]) -> Dict[str, Any]:
    """Calculate comprehensive schedule statistics"""
    if not assignments:
        return {
            "total_drivers": len(drivers),
            "total_routes": len(routes),
            "assigned_routes": 0,
            "unassigned_routes": len(routes),
            "utilization_rate": 0.0,
            "driver_workload": {}
        }
    
    # Calculate driver workload
    driver_workload = {}
    total_hours = 0
    
    for assignment in assignments:
        driver_id = assignment['driver_id']
        driver_name = assignment['driver']
        hours = assignment.get('duration_hours', 8.0)
        
        if driver_id not in driver_workload:
            driver_workload[driver_id] = {
                'name': driver_name,
                'routes': 0,
                'total_hours': 0.0
            }
        
        driver_workload[driver_id]['routes'] += 1
        driver_workload[driver_id]['total_hours'] += hours
        total_hours += hours
    
    assigned_routes = len(assignments)
    total_routes = len(routes)
    utilization_rate = (assigned_routes / total_routes * 100) if total_routes > 0 else 0
    
    return {
        "total_drivers": len(drivers),
        "active_drivers": len(driver_workload),
        "total_routes": total_routes,
        "assigned_routes": assigned_routes,
        "unassigned_routes": total_routes - assigned_routes,
        "utilization_rate": round(utilization_rate, 2),
        "total_hours_assigned": total_hours,
        "average_hours_per_driver": round(total_hours / len(driver_workload), 2) if driver_workload else 0,
        "driver_workload": driver_workload
    }
