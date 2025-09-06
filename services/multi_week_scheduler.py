"""
Multi-Week Scheduling Service
Handles replication of weekly route patterns for multiple consecutive weeks
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import json

from services.database import DatabaseService

logger = logging.getLogger(__name__)

# Define the standard weekly route pattern (42 routes total)
WEEKLY_ROUTE_PATTERN = {
    # Monday routes (8 routes)
    0: [  # Monday = weekday 0
        {"route_name": "431oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "432oS", "details": {"duration_hours": 12, "type": "regular"}},
        {"route_name": "433oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "434oS", "details": {"duration_hours": 10, "type": "regular"}},
        {"route_name": "437oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "438oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "439oS", "details": {"duration_hours": 12, "type": "regular"}},
        {"route_name": "440oS", "details": {"duration_hours": 3, "type": "regular"}},
    ],
    # Tuesday routes (8 routes)
    1: [  # Tuesday = weekday 1
        {"route_name": "431oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "432oS", "details": {"duration_hours": 12, "type": "regular"}},
        {"route_name": "433oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "434oS", "details": {"duration_hours": 10, "type": "regular"}},
        {"route_name": "437oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "438oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "439oS", "details": {"duration_hours": 12, "type": "regular"}},
        {"route_name": "440oS", "details": {"duration_hours": 3, "type": "regular"}},
    ],
    # Wednesday routes (8 routes)
    2: [  # Wednesday = weekday 2
        {"route_name": "431oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "432oS", "details": {"duration_hours": 12, "type": "regular"}},
        {"route_name": "433oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "434oS", "details": {"duration_hours": 10, "type": "regular"}},
        {"route_name": "437oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "438oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "439oS", "details": {"duration_hours": 12, "type": "regular"}},
        {"route_name": "440oS", "details": {"duration_hours": 3, "type": "regular"}},
    ],
    # Thursday routes (8 routes)
    3: [  # Thursday = weekday 3
        {"route_name": "431oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "432oS", "details": {"duration_hours": 12, "type": "regular"}},
        {"route_name": "433oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "434oS", "details": {"duration_hours": 10, "type": "regular"}},
        {"route_name": "437oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "438oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "439oS", "details": {"duration_hours": 12, "type": "regular"}},
        {"route_name": "440oS", "details": {"duration_hours": 3, "type": "regular"}},
    ],
    # Friday routes (8 routes)
    4: [  # Friday = weekday 4
        {"route_name": "431oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "432oS", "details": {"duration_hours": 12, "type": "regular"}},
        {"route_name": "433oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "434oS", "details": {"duration_hours": 10, "type": "regular"}},
        {"route_name": "437oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "438oS", "details": {"duration_hours": 11, "type": "regular"}},
        {"route_name": "439oS", "details": {"duration_hours": 12, "type": "regular"}},
        {"route_name": "440oS", "details": {"duration_hours": 3, "type": "regular"}},
    ],
    # Saturday routes (2 routes)
    5: [  # Saturday = weekday 5
        {"route_name": "451SA", "details": {"duration_hours": 10, "type": "regular"}},
        {"route_name": "452SA", "details": {"duration_hours": 10, "type": "regular"}},
    ],
    # Sunday routes (0 routes - drivers unavailable)
    6: []  # Sunday = weekday 6
}

# Day names for logging
DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


class MultiWeekScheduler:
    """Service for creating multi-week route schedules by replicating weekly patterns"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.db_service = DatabaseService(db_manager)
    
    def get_week_start(self, target_date: date) -> date:
        """Calculate the Monday of the week containing the given date"""
        days_since_monday = target_date.weekday()
        week_start = target_date - timedelta(days=days_since_monday)
        return week_start
    
    def get_week_end(self, week_start: date) -> date:
        """Calculate the Sunday of the week starting on the given Monday"""
        return week_start + timedelta(days=6)
    
    def generate_week_dates(self, week_start: date) -> List[date]:
        """Generate all 7 dates for a week starting from Monday"""
        return [week_start + timedelta(days=i) for i in range(7)]
    
    def calculate_multi_week_range(self, start_week_start: date, week_count: int) -> tuple[date, date]:
        """Calculate the overall date range for multiple weeks"""
        end_week_start = start_week_start + timedelta(weeks=week_count - 1)
        end_week_end = self.get_week_end(end_week_start)
        return start_week_start, end_week_end
    
    async def generate_multi_week_routes(self, start_week_start: date, week_count: int) -> List[Dict[str, Any]]:
        """Generate route data for multiple weeks using the standard weekly pattern"""
        try:
            logger.info(f"Generating routes for {week_count} weeks starting {start_week_start}")
            
            all_routes = []
            
            for week_num in range(week_count):
                # Calculate the Monday of this week
                current_week_start = start_week_start + timedelta(weeks=week_num)
                week_dates = self.generate_week_dates(current_week_start)
                
                logger.info(f"Week {week_num + 1}: {current_week_start} to {self.get_week_end(current_week_start)}")
                
                # Generate routes for each day of this week
                for day_index, current_date in enumerate(week_dates):
                    day_name = DAY_NAMES[day_index]
                    routes_for_day = WEEKLY_ROUTE_PATTERN.get(day_index, [])
                    
                    logger.debug(f"  {day_name} {current_date}: {len(routes_for_day)} routes")
                    
                    # Create route entries for this day
                    for route_template in routes_for_day:
                        route_entry = {
                            "date": current_date,
                            "route_name": route_template["route_name"],
                            "day_of_week": day_name,
                            "details": route_template["details"].copy()  # Copy to avoid reference issues
                        }
                        all_routes.append(route_entry)
            
            logger.info(f"Generated {len(all_routes)} total routes for {week_count} weeks")
            return all_routes
            
        except Exception as e:
            logger.error(f"Failed to generate multi-week routes: {e}")
            return []
    
    async def create_multi_week_routes_in_db(self, start_week_start: date, week_count: int) -> Dict[str, Any]:
        """Create multi-week routes in the database"""
        try:
            # Generate route data
            routes_data = await self.generate_multi_week_routes(start_week_start, week_count)
            if not routes_data:
                return {"success": False, "message": "Failed to generate routes", "routes_created": 0}
            
            # Get the date range for cleanup
            range_start, range_end = self.calculate_multi_week_range(start_week_start, week_count)
            
            # Clear existing routes in the date range
            async with self.db_manager.get_connection() as conn:
                # Clear existing routes for the date range
                await conn.execute("""
                    DELETE FROM routes 
                    WHERE date BETWEEN $1 AND $2
                """, range_start, range_end)
                logger.info(f"Cleared existing routes from {range_start} to {range_end}")
                
                # Get the next available route_id
                next_id = await conn.fetchval("SELECT COALESCE(MAX(route_id), 0) + 1 FROM routes")
                
                # Insert new routes
                routes_created = 0
                for route_data in routes_data:
                    await conn.execute("""
                        INSERT INTO routes (route_id, date, route_name, day_of_week, details, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, 
                    next_id,
                    route_data["date"],
                    route_data["route_name"],
                    route_data["day_of_week"],
                    json.dumps(route_data["details"]),
                    datetime.now()
                    )
                    routes_created += 1
                    next_id += 1
                
                logger.info(f"Successfully created {routes_created} routes in database")
                
                return {
                    "success": True,
                    "message": f"Created {routes_created} routes for {week_count} weeks",
                    "routes_created": routes_created,
                    "weeks_generated": week_count,
                    "date_range": {
                        "start": range_start.strftime('%Y-%m-%d'),
                        "end": range_end.strftime('%Y-%m-%d')
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to create multi-week routes in database: {e}")
            return {
                "success": False,
                "message": f"Database error: {str(e)}",
                "routes_created": 0
            }
    
    async def generate_multi_week_availability(self, start_week_start: date, week_count: int) -> Dict[str, Any]:
        """Generate driver availability for multiple weeks (weekdays available, Sundays unavailable)"""
        try:
            # Get all drivers
            drivers = await self.db_service.get_drivers()
            if not drivers:
                return {"success": False, "message": "No drivers found", "availability_created": 0}
            
            # Calculate date range
            range_start, range_end = self.calculate_multi_week_range(start_week_start, week_count)
            
            availability_created = 0
            async with self.db_manager.get_connection() as conn:
                # Clear existing availability for the date range
                await conn.execute("""
                    DELETE FROM driver_availability 
                    WHERE date BETWEEN $1 AND $2
                """, range_start, range_end)
                logger.info(f"Cleared existing availability from {range_start} to {range_end}")
                
                # Generate availability for each week
                for week_num in range(week_count):
                    current_week_start = start_week_start + timedelta(weeks=week_num)
                    week_dates = self.generate_week_dates(current_week_start)
                    
                    for driver in drivers:
                        driver_id = driver['driver_id']
                        
                        for day_index, current_date in enumerate(week_dates):
                            # Monday-Saturday available, Sunday unavailable
                            is_available = day_index != 6  # Sunday = day_index 6
                            
                            await conn.execute("""
                                INSERT INTO driver_availability (driver_id, date, available)
                                VALUES ($1, $2, $3)
                            """, driver_id, current_date, is_available)
                            availability_created += 1
                
                logger.info(f"Created {availability_created} availability records for {len(drivers)} drivers across {week_count} weeks")
                
                return {
                    "success": True,
                    "message": f"Created availability for {len(drivers)} drivers across {week_count} weeks",
                    "availability_created": availability_created,
                    "drivers_count": len(drivers),
                    "weeks_generated": week_count
                }
                
        except Exception as e:
            logger.error(f"Failed to generate multi-week availability: {e}")
            return {
                "success": False,
                "message": f"Availability generation error: {str(e)}",
                "availability_created": 0
            }