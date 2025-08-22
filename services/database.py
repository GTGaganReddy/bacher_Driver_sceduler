import json
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
import asyncpg
from schemas.models import Driver, Route, DriverAvailability
from config.settings import settings

class DatabaseService:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    async def get_drivers(self) -> List[Dict]:
        """Get all drivers"""
        async with self.db_manager.get_connection() as conn:
            rows = await conn.fetch("SELECT * FROM drivers ORDER BY name")
            return [dict(row) for row in rows]
    
    async def create_driver(self, name: str) -> int:
        """Create a new driver"""
        async with self.db_manager.get_connection() as conn:
            driver_id = await conn.fetchval(
                "INSERT INTO drivers (name) VALUES ($1) RETURNING driver_id",
                name
            )
            return driver_id
    
    async def delete_driver(self, driver_id: int):
        """Delete a driver"""
        async with self.db_manager.get_connection() as conn:
            await conn.execute("DELETE FROM drivers WHERE driver_id = $1", driver_id)
    
    async def get_routes_by_date_range(self, start_date: date, end_date: date) -> List[Dict]:
        """Get routes within date range"""
        async with self.db_manager.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT * FROM routes 
                WHERE date BETWEEN $1 AND $2
                ORDER BY date, route_name
            """, start_date, end_date)
            return [dict(row) for row in rows]
    
    async def create_route(self, route_date: date, route_name: str, details: Optional[Dict] = None) -> int:
        """Create a new route"""
        async with self.db_manager.get_connection() as conn:
            route_id = await conn.fetchval("""
                INSERT INTO routes (date, route_name, details) 
                VALUES ($1, $2, $3) RETURNING route_id
            """, route_date, route_name, json.dumps(details or {}))
            return route_id
    
    async def update_route(self, route_id: int, route_date: date, route_name: str, details: Optional[Dict] = None):
        """Update an existing route"""
        async with self.db_manager.get_connection() as conn:
            await conn.execute("""
                UPDATE routes 
                SET date = $1, route_name = $2, details = $3 
                WHERE route_id = $4
            """, route_date, route_name, json.dumps(details or {}), route_id)
    
    async def delete_route(self, route_id: int):
        """Delete a route"""
        async with self.db_manager.get_connection() as conn:
            await conn.execute("DELETE FROM routes WHERE route_id = $1", route_id)
    
    async def get_availability_by_date_range(self, start_date: date, end_date: date) -> List[Dict]:
        """Get driver availability within date range"""
        async with self.db_manager.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT da.*, d.name 
                FROM driver_availability da
                JOIN drivers d ON da.driver_id = d.driver_id
                WHERE da.date BETWEEN $1 AND $2
                ORDER BY da.date, d.name
            """, start_date, end_date)
            return [dict(row) for row in rows]

    async def get_fixed_assignments_by_date_range(self, start_date: date, end_date: date) -> List[Dict]:
        """Get fixed assignments within date range"""
        print(f"DATABASE: Fetching fixed assignments for {start_date} to {end_date}")
        async with self.db_manager.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT fa.*, d.name as driver_name, r.route_name
                FROM fixed_assignments fa
                JOIN drivers d ON fa.driver_id = d.driver_id
                JOIN routes r ON fa.route_id = r.route_id
                WHERE fa.date BETWEEN $1 AND $2
                ORDER BY fa.date, fa.driver_id
            """, start_date, end_date)
            result = [dict(row) for row in rows]
            print(f"DATABASE: Fetched {len(result)} fixed assignments")
            if result:
                print(f"DATABASE: Sample fixed assignment: {result[0]}")
            return result
    
    async def update_driver_availability(self, driver_id: int, availability_date: date, available: bool):
        """Update driver availability"""
        async with self.db_manager.get_connection() as conn:
            await conn.execute("""
                INSERT INTO driver_availability (driver_id, date, available)
                VALUES ($1, $2, $3)
                ON CONFLICT (driver_id, date)
                DO UPDATE SET available = $3
            """, driver_id, availability_date, available)
    
    async def save_assignments(self, week_start: date, assignments: List[Dict]):
        """Save optimized assignments for a week"""
        async with self.db_manager.get_connection() as conn:
            # Delete existing assignments for this week first
            await conn.execute("DELETE FROM assignments WHERE week_start = $1", week_start)
            # Insert new assignments
            await conn.execute("""
                INSERT INTO assignments (week_start, assignments)
                VALUES ($1, $2)
            """, week_start, json.dumps(assignments))
    
    async def get_assignments(self, week_start: date) -> Optional[List[Dict]]:
        """Get assignments for a specific week"""
        async with self.db_manager.get_connection() as conn:
            result = await conn.fetchval(
                "SELECT assignments FROM assignments WHERE week_start = $1",
                week_start
            )
            return json.loads(result) if result else None
