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
    
    async def create_route(self, route_date: date, route_name: str, day_of_week: Optional[str] = None, details: Optional[Dict] = None) -> int:
        """Create a new route"""
        async with self.db_manager.get_connection() as conn:
            # Find next available route_id to avoid sequence/pooling issues
            next_id = await conn.fetchval("""
                SELECT COALESCE(MAX(route_id), 0) + 1 FROM routes
            """)
            
            # Auto-derive day_of_week if not provided
            if day_of_week is None:
                weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_of_week = weekday_names[route_date.weekday()]
            
            route_id = await conn.fetchval("""
                INSERT INTO routes (route_id, date, route_name, day_of_week, details) 
                VALUES ($1, $2, $3, $4, $5) RETURNING route_id
            """, next_id, route_date, route_name, day_of_week, json.dumps(details or {}))
            return route_id
    
    async def update_route(self, route_id: int, route_date: date, route_name: str, day_of_week: Optional[str] = None, details: Optional[Dict] = None):
        """Update an existing route"""
        async with self.db_manager.get_connection() as conn:
            # Auto-derive day_of_week if not provided
            if day_of_week is None:
                weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_of_week = weekday_names[route_date.weekday()]
                
            await conn.execute("""
                UPDATE routes 
                SET date = $1, route_name = $2, day_of_week = $3, details = $4 
                WHERE route_id = $5
            """, route_date, route_name, day_of_week, json.dumps(details or {}), route_id)
    
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
        try:
            print(f"DATABASE: Fetching fixed assignments for {start_date} to {end_date}")
            async with self.db_manager.get_connection() as conn:
                # First, check if the table exists and has data
                count = await conn.fetchval("SELECT COUNT(*) FROM fixed_assignments")
                print(f"DATABASE: Total fixed assignments in table: {count}")
                
                rows = await conn.fetch("""
                    SELECT fa.*, d.name as driver_name, r.route_name
                    FROM fixed_assignments fa
                    JOIN drivers d ON fa.driver_id = d.driver_id
                    JOIN routes r ON fa.route_id = r.route_id
                    WHERE fa.date BETWEEN $1 AND $2
                    ORDER BY fa.date, fa.driver_id
                """, start_date, end_date)
                result = [dict(row) for row in rows]
                print(f"DATABASE: Query returned {len(result)} fixed assignments")
                if result:
                    print(f"DATABASE: Sample fixed assignment: {result[0]}")
                return result
        except Exception as e:
            print(f"DATABASE ERROR: Failed to fetch fixed assignments: {e}")
            return []
    
    async def get_all_fixed_assignments(self) -> List[Dict]:
        """Get all fixed assignments with driver and route details"""
        try:
            async with self.db_manager.get_connection() as conn:
                rows = await conn.fetch("""
                    SELECT fa.*, d.name as driver_name, r.route_name
                    FROM fixed_assignments fa
                    JOIN drivers d ON fa.driver_id = d.driver_id
                    JOIN routes r ON fa.route_id = r.route_id
                    ORDER BY fa.date, d.name
                """)
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"DATABASE ERROR: Failed to fetch all fixed assignments: {e}")
            return []
    
    async def add_fixed_assignment(self, driver_id: int, route_id: int, assignment_date: date) -> bool:
        """Add a new fixed assignment"""
        try:
            async with self.db_manager.get_connection() as conn:
                # Check if this exact combination already exists
                existing = await conn.fetchval("""
                    SELECT id FROM fixed_assignments 
                    WHERE driver_id = $1 AND route_id = $2 AND date = $3
                """, driver_id, route_id, assignment_date)
                
                if existing:
                    print(f"DATABASE: Fixed assignment already exists with ID {existing}")
                    return True
                
                # Delete any existing assignment for this driver on this date
                await conn.execute("""
                    DELETE FROM fixed_assignments 
                    WHERE driver_id = $1 AND date = $2
                """, driver_id, assignment_date)
                
                # Insert new assignment
                await conn.execute("""
                    INSERT INTO fixed_assignments (driver_id, route_id, date)
                    VALUES ($1, $2, $3)
                """, driver_id, route_id, assignment_date)
                return True
        except Exception as e:
            print(f"DATABASE ERROR: Failed to add fixed assignment: {e}")
            return False
    
    async def delete_fixed_assignment(self, driver_id: int, assignment_date: date) -> bool:
        """Delete a fixed assignment"""
        try:
            async with self.db_manager.get_connection() as conn:
                result = await conn.execute("""
                    DELETE FROM fixed_assignments 
                    WHERE driver_id = $1 AND date = $2
                """, driver_id, assignment_date)
                return True
        except Exception as e:
            print(f"DATABASE ERROR: Failed to delete fixed assignment: {e}")
            return False
    
    async def get_driver_by_name(self, driver_name: str) -> Optional[Dict]:
        """Get driver by name"""
        async with self.db_manager.get_connection() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM drivers WHERE name = $1
            """, driver_name)
            return dict(row) if row else None
    
    async def get_route_by_name_and_date(self, route_name: str, route_date: date) -> Optional[Dict]:
        """Get route by name and date"""
        async with self.db_manager.get_connection() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM routes WHERE route_name = $1 AND date = $2
            """, route_name, route_date)
            return dict(row) if row else None
    
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
