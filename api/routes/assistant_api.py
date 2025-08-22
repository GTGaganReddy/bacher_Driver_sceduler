"""
Assistant API endpoints for external integrations.
Provides complete workflow: DB operations -> OR-Tools optimization -> Google Sheets update.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging
from pydantic import BaseModel, Field

from services.database import DatabaseService
from services.google_sheets import GoogleSheetsService
from services.optimizer import SchedulingOptimizer
from services.enhanced_optimizer import run_enhanced_ortools_optimization
from api.dependencies import db_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/assistant", tags=["Assistant API"])


# Request Models
class WeeklyOptimizationRequest(BaseModel):
    week_start: str = Field(..., description="Week start date (YYYY-MM-DD)")


class AvailabilityUpdateRequest(BaseModel):
    driver_name: str = Field(..., description="Driver name from database")
    updates: List[Dict[str, Any]] = Field(..., description="Date/availability updates")
    week_start: str = Field(..., description="Week start for reoptimization")


class SimpleAvailabilityUpdateRequest(BaseModel):
    driver_name: str = Field(..., description="Driver name from database")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    available: bool = Field(..., description="True if available, False if unavailable")


class RouteRequest(BaseModel):
    route_name: str = Field(..., description="Route name (e.g., '431oS')")
    date: str = Field(..., description="Route date (YYYY-MM-DD)")
    duration_hours: float = Field(..., description="Duration in hours")
    route_type: str = Field(default="regular")
    day_of_week: str = Field(..., description="Day of week")
    week_start: str = Field(..., description="Week start for reoptimization")


class AddSingleRouteRequest(BaseModel):
    route_name: str = Field(..., description="Route name (e.g., '500')")
    date: str = Field(..., description="Route date (YYYY-MM-DD)")
    duration_hours: float = Field(..., description="Duration in hours")


class RemoveRouteRequest(BaseModel):
    route_name: str = Field(..., description="Route name to remove (e.g., '500')")
    date: str = Field(..., description="Route date (YYYY-MM-DD)")


@router.post("/optimize-week")
async def optimize_week(request: WeeklyOptimizationRequest):
    """Complete weekly optimization: DB -> OR-Tools -> Google Sheets"""
    try:
        logger.info(f"Assistant API: Weekly optimization for {request.week_start}")
        
        week_start = datetime.strptime(request.week_start, '%Y-%m-%d').date()
        week_end = week_start + timedelta(days=6)
        
        db_service = DatabaseService(db_manager)
        sheets_service = GoogleSheetsService()
        
        # Fetch all data
        drivers = await db_service.get_drivers()
        routes = await db_service.get_routes_by_date_range(week_start, week_end)
        availability = await db_service.get_availability_by_date_range(week_start, week_end)
        
        if not drivers or not routes:
            raise HTTPException(status_code=404, detail="Missing drivers or routes data")
        
        # Run ENHANCED OR-Tools optimization with consecutive hours constraint
        optimization_result = run_enhanced_ortools_optimization(drivers, routes, availability)
        
        # Generate complete driver grid for Google Sheets
        week_dates = [(week_start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
        
        # Update Google Sheets with complete driver grid
        sheets_result = await sheets_service.update_sheet(
            optimization_result,
            all_drivers=drivers,
            all_dates=week_dates
        )
        sheets_success = sheets_result is not None  # Success if result returned
        
        # Save results to database
        assignments = optimization_result.get('assignments', {})
        await db_service.save_assignments(week_start, list(assignments.values()))
        
        return {
            "status": "success",
            "week_start": request.week_start,
            "total_assignments": sum(len(day_assignments) for day_assignments in assignments.values()),
            "total_routes": len(routes),
            "google_sheets_updated": sheets_success,
            "solver_status": optimization_result.get('solver_status')
        }
        
    except Exception as e:
        logger.error(f"Weekly optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-availability")
async def update_availability(request: AvailabilityUpdateRequest):
    """Update driver availability -> Rerun optimization -> Update sheets"""
    try:
        logger.info(f"Assistant API: Updating availability for {request.driver_name}")
        
        week_start = datetime.strptime(request.week_start, '%Y-%m-%d').date()
        week_end = week_start + timedelta(days=6)
        
        db_service = DatabaseService(db_manager)
        sheets_service = GoogleSheetsService()
        
        # Find driver by name
        drivers = await db_service.get_drivers()
        target_driver = None
        for driver in drivers:
            if driver['name'] == request.driver_name:
                target_driver = driver
                break
        
        if not target_driver:
            raise HTTPException(status_code=404, detail=f"Driver '{request.driver_name}' not found")
        
        # Update availability in database
        driver_id = target_driver['driver_id']
        updates_made = 0
        
        for update in request.updates:
            try:
                update_date = datetime.strptime(update['date'], '%Y-%m-%d').date()
                available = update['available']
                await db_service.update_driver_availability(driver_id, update_date, available)
                updates_made += 1
                logger.info(f"Updated {request.driver_name} availability on {update_date}: {available}")
            except (ValueError, KeyError) as e:
                logger.warning(f"Invalid update: {e}")
                continue
        
        if updates_made == 0:
            raise HTTPException(status_code=400, detail="No valid updates processed")
        
        # Rerun complete optimization
        routes = await db_service.get_routes_by_date_range(week_start, week_end)
        availability = await db_service.get_availability_by_date_range(week_start, week_end)
        
        optimization_result = run_enhanced_ortools_optimization(drivers, routes, availability)
        
        # Update Google Sheets
        week_dates = [(week_start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
        sheets_result = await sheets_service.update_sheet(
            optimization_result,
            all_drivers=drivers,
            all_dates=week_dates
        )
        sheets_success = sheets_result is not None
        
        # Save results
        assignments = optimization_result.get('assignments', {})
        await db_service.save_assignments(week_start, list(assignments.values()))
        
        return {
            "status": "success",
            "driver_updated": request.driver_name,
            "updates_applied": updates_made,
            "total_assignments": sum(len(day_assignments) for day_assignments in assignments.values()),
            "google_sheets_updated": sheets_success
        }
        
    except Exception as e:
        logger.error(f"Availability update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-driver-availability")
async def update_single_driver_availability(request: SimpleAvailabilityUpdateRequest):
    """Simplified endpoint: Update single driver availability -> Rerun optimization -> Update sheets"""
    try:
        logger.info(f"Assistant API: Simple update for {request.driver_name} on {request.date}")
        
        # Convert to the format expected by the main update_availability function
        availability_request = AvailabilityUpdateRequest(
            driver_name=request.driver_name,
            updates=[{"date": request.date, "available": request.available}],
            week_start="2025-07-07"  # Default to July 2025 week
        )
        
        # Call the main availability update function
        return await update_availability(availability_request)
        
    except Exception as e:
        logger.error(f"Simple availability update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-route")
async def add_route(request: RouteRequest):
    """Add new route -> Rerun optimization -> Update sheets"""
    try:
        logger.info(f"Assistant API: Adding route {request.route_name} for {request.date}")
        
        route_date = datetime.strptime(request.date, '%Y-%m-%d').date()
        week_start = datetime.strptime(request.week_start, '%Y-%m-%d').date()
        week_end = week_start + timedelta(days=6)
        
        db_service = DatabaseService(db_manager)
        sheets_service = GoogleSheetsService()
        
        # Create route details for database
        route_details = {
            "route_code": request.route_name,
            "duration": f"{int(request.duration_hours)}:{int((request.duration_hours % 1) * 60):02d}",
            "type": request.route_type
        }
        
        # Add route to database
        route_id = await db_service.create_route(route_date, request.route_name, route_details)
        logger.info(f"Created route {request.route_name} with ID {route_id}")
        
        # Rerun complete optimization with new route
        drivers = await db_service.get_drivers()
        routes = await db_service.get_routes_by_date_range(week_start, week_end)
        availability = await db_service.get_availability_by_date_range(week_start, week_end)
        
        optimization_result = run_enhanced_ortools_optimization(drivers, routes, availability)
        
        # Update Google Sheets
        week_dates = [(week_start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
        sheets_result = await sheets_service.update_sheet(
            optimization_result,
            all_drivers=drivers,
            all_dates=week_dates
        )
        sheets_success = sheets_result is not None
        
        # Save results
        assignments = optimization_result.get('assignments', {})
        await db_service.save_assignments(week_start, list(assignments.values()))
        
        return {
            "status": "success",
            "route_added": {
                "id": route_id,
                "name": request.route_name,
                "date": request.date,
                "duration_hours": request.duration_hours
            },
            "total_assignments": sum(len(day_assignments) for day_assignments in assignments.values()),
            "total_routes": len(routes),
            "google_sheets_updated": sheets_success
        }
        
    except Exception as e:
        logger.error(f"Route addition failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-single-route")
async def add_single_route(request: AddSingleRouteRequest):
    """Simplified endpoint to add a single route"""
    try:
        logger.info(f"Assistant API: Adding single route {request.route_name} for {request.date}")
        
        # Convert date to day_of_week
        date_obj = datetime.strptime(request.date, "%Y-%m-%d")
        day_of_week = date_obj.strftime("%A").lower()
        
        # Use existing logic with July 2025 week
        route_request = RouteRequest(
            route_name=request.route_name,
            date=request.date,
            duration_hours=request.duration_hours,
            day_of_week=day_of_week,
            week_start="2025-07-07"  # Default to July 2025 week
        )
        
        return await add_route(route_request)
        
    except Exception as e:
        logger.error(f"Single route addition failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remove-route")
async def remove_route(request: RemoveRouteRequest):
    """Remove a route and rerun optimization"""
    try:
        logger.info(f"Assistant API: Removing route {request.route_name} from {request.date}")
        
        db_service = DatabaseService(db_manager)
        sheets_service = GoogleSheetsService()
        
        # Convert date string to date object
        route_date = datetime.strptime(request.date, "%Y-%m-%d").date()
        
        # Remove the route from database
        async with db_manager.get_connection() as conn:
            deleted_route = await conn.fetchrow(
                "DELETE FROM routes WHERE route_name = $1 AND date = $2 RETURNING route_id",
                request.route_name, route_date
            )
            
            if not deleted_route:
                raise HTTPException(status_code=404, detail=f"Route '{request.route_name}' on {request.date} not found")
            
            logger.info(f"Deleted route {request.route_name} (ID: {deleted_route['route_id']}) from {request.date}")
        
        # Get fresh data and reoptimize
        week_start = datetime.strptime('2025-07-07', '%Y-%m-%d').date()
        week_end = week_start + timedelta(days=6)
        
        drivers = await db_service.get_drivers()
        routes = await db_service.get_routes_by_date_range(week_start, week_end)
        availability = await db_service.get_availability_by_date_range(week_start, week_end)
        
        optimization_result = run_enhanced_ortools_optimization(drivers, routes, availability)
        
        # Update Google Sheets
        week_dates = [(week_start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
        sheets_result = await sheets_service.update_sheet(
            optimization_result,
            all_drivers=drivers,
            all_dates=week_dates
        )
        sheets_success = sheets_result is not None
        
        # Save results
        assignments = optimization_result.get('assignments', {})
        await db_service.save_assignments(week_start, list(assignments.values()))
        
        return {
            "status": "success",
            "route_removed": {
                "name": request.route_name,
                "date": request.date,
                "id": deleted_route['route_id']
            },
            "total_assignments": sum(len(day_assignments) for day_assignments in assignments.values()),
            "total_routes": len(routes),
            "google_sheets_updated": sheets_success
        }
        
    except Exception as e:
        logger.error(f"Route removal failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_system():
    """Reset system to initial state - clear assignments and reset availability"""
    try:
        logger.info("Assistant API: Resetting system to initial state")
        
        db_service = DatabaseService(db_manager)
        
        # Clear all assignments
        async with db_manager.get_connection() as conn:
            await conn.execute("DELETE FROM assignments")
            logger.info("Cleared all assignments")
            
            # Clear routes that were added via API (created after initial system setup)
            # Only remove routes added after August 11, 2025 to preserve original system data
            await conn.execute("""
                DELETE FROM routes 
                WHERE date BETWEEN '2025-07-07' AND '2025-07-13' 
                AND created_at > '2025-08-11 21:10:00'
            """)
            logger.info("Cleared manually added routes (preserving original system routes)")
            
            # Reset all driver availability to true (available) for July 7-13, 2025
            # Keep Sunday (2025-07-13) as unavailable for all drivers
            await conn.execute("""
                UPDATE driver_availability 
                SET available = true 
                WHERE date BETWEEN '2025-07-07' AND '2025-07-12'
            """)
            
            # Ensure Sunday remains unavailable for all drivers
            await conn.execute("""
                UPDATE driver_availability 
                SET available = false 
                WHERE date = '2025-07-13'
            """)
            
            logger.info("Reset driver availability - weekdays available, Sunday unavailable")
        
        # Get fresh data for verification
        drivers = await db_service.get_drivers()
        routes = await db_service.get_routes_by_date_range(
            datetime.strptime('2025-07-07', '%Y-%m-%d').date(),
            datetime.strptime('2025-07-13', '%Y-%m-%d').date()
        )
        
        # Run optimization with reset state and update Google Sheets
        optimizer = SchedulingOptimizer()
        sheets_service = GoogleSheetsService()
        
        # Get driver availability for the reset state
        availability = await db_service.get_availability_by_date_range(
            datetime.strptime('2025-07-07', '%Y-%m-%d').date(),
            datetime.strptime('2025-07-13', '%Y-%m-%d').date()
        )
        
        if routes:
            # Run ENHANCED optimization with consecutive hours constraint
            optimization_result = run_enhanced_ortools_optimization(drivers, routes, availability)
            
            # Update Google Sheets with reset state
            week_start = datetime.strptime('2025-07-07', '%Y-%m-%d').date()
            week_dates = [(week_start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
            sheets_result = await sheets_service.update_sheet(
                optimization_result,
                all_drivers=drivers,
                all_dates=week_dates
            )
            sheets_updated = sheets_result is not None
            
            # Save optimization results
            assignments = optimization_result.get('assignments', {})
            await db_service.save_assignments(week_start, list(assignments.values()))
            
            logger.info(f"Reset complete: optimized {len(routes)} routes, updated sheets: {sheets_updated}")
        else:
            # No routes - just clear sheets with empty data
            week_start = datetime.strptime('2025-07-07', '%Y-%m-%d').date()
            week_dates = [(week_start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
            empty_result = {"assignments": {}, "stats": {"total_routes": 0, "assigned_routes": 0}}
            sheets_result = await sheets_service.update_sheet(
                empty_result,
                all_drivers=drivers,
                all_dates=week_dates
            )
            sheets_updated = sheets_result is not None
            logger.info(f"Reset complete: no routes to optimize, cleared sheets: {sheets_updated}")
        
        return {
            "status": "success",
            "message": "System reset to initial state and optimization completed",
            "drivers_count": len(drivers),
            "routes_count": len(routes),
            "assignments_cleared": True,
            "availability_reset": True,
            "routes_reset": True,
            "optimization_run": True,
            "sheets_updated": sheets_updated
        }
        
    except Exception as e:
        logger.error(f"System reset failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@router.get("/status")
async def get_status():
    """System status check"""
    try:
        db_service = DatabaseService(db_manager)
        drivers = await db_service.get_drivers()
        
        return {
            "status": "operational",
            "drivers_count": len(drivers),
            "or_tools_enabled": True,
            "google_sheets_integration": True
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}