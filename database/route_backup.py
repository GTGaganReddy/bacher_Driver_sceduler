"""
Route Backup and Recovery System
Provides mechanisms to backup and restore original system routes
"""

from datetime import date, datetime
from typing import List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

# Default fixed assignments for the system (36 assignments)
DEFAULT_FIXED_ASSIGNMENTS = [
    # Hinteregger, Manfred (driver_id: 4) -> 431oS Monday to Friday
    {"driver_id": 4, "route_id": 1, "date": "2025-07-07"},   # Monday 431oS
    {"driver_id": 4, "route_id": 9, "date": "2025-07-08"},   # Tuesday 431oS
    {"driver_id": 4, "route_id": 17, "date": "2025-07-09"},  # Wednesday 431oS
    {"driver_id": 4, "route_id": 25, "date": "2025-07-10"},  # Thursday 431oS
    {"driver_id": 4, "route_id": 33, "date": "2025-07-11"},  # Friday 431oS
    
    # Kandolf, Alfred (driver_id: 5) -> 434oS Monday to Friday
    {"driver_id": 5, "route_id": 4, "date": "2025-07-07"},   # Monday 434oS
    {"driver_id": 5, "route_id": 12, "date": "2025-07-08"},  # Tuesday 434oS
    {"driver_id": 5, "route_id": 20, "date": "2025-07-09"},  # Wednesday 434oS
    {"driver_id": 5, "route_id": 28, "date": "2025-07-10"},  # Thursday 434oS
    {"driver_id": 5, "route_id": 36, "date": "2025-07-11"},  # Friday 434oS
    
    # Madrutter, Anton (driver_id: 8) -> 439oS Monday to Friday
    {"driver_id": 8, "route_id": 7, "date": "2025-07-07"},   # Monday 439oS
    {"driver_id": 8, "route_id": 15, "date": "2025-07-08"},  # Tuesday 439oS
    {"driver_id": 8, "route_id": 23, "date": "2025-07-09"},  # Wednesday 439oS
    {"driver_id": 8, "route_id": 31, "date": "2025-07-10"},  # Thursday 439oS
    {"driver_id": 8, "route_id": 39, "date": "2025-07-11"},  # Friday 439oS
    
    # Niederbichler, Daniel (driver_id: 9) -> 433oS Monday to Friday
    {"driver_id": 9, "route_id": 3, "date": "2025-07-07"},   # Monday 433oS
    {"driver_id": 9, "route_id": 11, "date": "2025-07-08"},  # Tuesday 433oS
    {"driver_id": 9, "route_id": 19, "date": "2025-07-09"},  # Wednesday 433oS
    {"driver_id": 9, "route_id": 27, "date": "2025-07-10"},  # Thursday 433oS
    {"driver_id": 9, "route_id": 35, "date": "2025-07-11"},  # Friday 433oS
    
    # Rauter, Agnes Zita (driver_id: 12) -> 432oS Monday to Friday
    {"driver_id": 12, "route_id": 2, "date": "2025-07-07"},  # Monday 432oS
    {"driver_id": 12, "route_id": 10, "date": "2025-07-08"}, # Tuesday 432oS
    {"driver_id": 12, "route_id": 18, "date": "2025-07-09"}, # Wednesday 432oS
    {"driver_id": 12, "route_id": 26, "date": "2025-07-10"}, # Thursday 432oS
    {"driver_id": 12, "route_id": 34, "date": "2025-07-11"}, # Friday 432oS
    
    # Simon, Otto (driver_id: 13) -> 437oS Monday to Friday
    {"driver_id": 13, "route_id": 5, "date": "2025-07-07"},  # Monday 437oS
    {"driver_id": 13, "route_id": 13, "date": "2025-07-08"}, # Tuesday 437oS
    {"driver_id": 13, "route_id": 21, "date": "2025-07-09"}, # Wednesday 437oS
    {"driver_id": 13, "route_id": 29, "date": "2025-07-10"}, # Thursday 437oS
    {"driver_id": 13, "route_id": 37, "date": "2025-07-11"}, # Friday 437oS
    
    # Struckl, Stefan (driver_id: 15) -> 438oS Monday to Friday
    {"driver_id": 15, "route_id": 6, "date": "2025-07-07"},  # Monday 438oS
    {"driver_id": 15, "route_id": 14, "date": "2025-07-08"}, # Tuesday 438oS
    {"driver_id": 15, "route_id": 22, "date": "2025-07-09"}, # Wednesday 438oS
    {"driver_id": 15, "route_id": 30, "date": "2025-07-10"}, # Thursday 438oS
    {"driver_id": 15, "route_id": 38, "date": "2025-07-11"}, # Friday 438oS
    
    # Klagenfurt - Fahrer (driver_id: 20) -> 451SA Saturday
    {"driver_id": 20, "route_id": 41, "date": "2025-07-12"}  # Saturday 451SA
]

# Original system routes for July 7-13, 2025 (42 routes)
ORIGINAL_ROUTES_BACKUP = [
    # Monday 2025-07-07 (8 routes)
    {"date": "2025-07-07", "route_name": "431oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-07", "route_name": "432oS", "details": {"duration_hours": 12, "type": "regular"}},
    {"date": "2025-07-07", "route_name": "433oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-07", "route_name": "434oS", "details": {"duration_hours": 10, "type": "regular"}},
    {"date": "2025-07-07", "route_name": "437oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-07", "route_name": "438oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-07", "route_name": "439oS", "details": {"duration_hours": 12, "type": "regular"}},
    {"date": "2025-07-07", "route_name": "440oS", "details": {"duration_hours": 3, "type": "regular"}},
    
    # Tuesday 2025-07-08 (8 routes)
    {"date": "2025-07-08", "route_name": "431oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-08", "route_name": "432oS", "details": {"duration_hours": 12, "type": "regular"}},
    {"date": "2025-07-08", "route_name": "433oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-08", "route_name": "434oS", "details": {"duration_hours": 10, "type": "regular"}},
    {"date": "2025-07-08", "route_name": "437oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-08", "route_name": "438oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-08", "route_name": "439oS", "details": {"duration_hours": 12, "type": "regular"}},
    {"date": "2025-07-08", "route_name": "440oS", "details": {"duration_hours": 3, "type": "regular"}},
    
    # Wednesday 2025-07-09 (8 routes)
    {"date": "2025-07-09", "route_name": "431oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-09", "route_name": "432oS", "details": {"duration_hours": 12, "type": "regular"}},
    {"date": "2025-07-09", "route_name": "433oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-09", "route_name": "434oS", "details": {"duration_hours": 10, "type": "regular"}},
    {"date": "2025-07-09", "route_name": "437oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-09", "route_name": "438oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-09", "route_name": "439oS", "details": {"duration_hours": 12, "type": "regular"}},
    {"date": "2025-07-09", "route_name": "440oS", "details": {"duration_hours": 3, "type": "regular"}},
    
    # Thursday 2025-07-10 (8 routes)
    {"date": "2025-07-10", "route_name": "431oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-10", "route_name": "432oS", "details": {"duration_hours": 12, "type": "regular"}},
    {"date": "2025-07-10", "route_name": "433oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-10", "route_name": "434oS", "details": {"duration_hours": 10, "type": "regular"}},
    {"date": "2025-07-10", "route_name": "437oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-10", "route_name": "438oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-10", "route_name": "439oS", "details": {"duration_hours": 12, "type": "regular"}},
    {"date": "2025-07-10", "route_name": "440oS", "details": {"duration_hours": 3, "type": "regular"}},
    
    # Friday 2025-07-11 (8 routes)
    {"date": "2025-07-11", "route_name": "431oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-11", "route_name": "432oS", "details": {"duration_hours": 12, "type": "regular"}},
    {"date": "2025-07-11", "route_name": "433oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-11", "route_name": "434oS", "details": {"duration_hours": 10, "type": "regular"}},
    {"date": "2025-07-11", "route_name": "437oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-11", "route_name": "438oS", "details": {"duration_hours": 11, "type": "regular"}},
    {"date": "2025-07-11", "route_name": "439oS", "details": {"duration_hours": 12, "type": "regular"}},
    {"date": "2025-07-11", "route_name": "440oS", "details": {"duration_hours": 3, "type": "regular"}},
    
    # Saturday 2025-07-12 (2 routes)
    {"date": "2025-07-12", "route_name": "451SA", "details": {"duration_hours": 10, "type": "regular"}},
    {"date": "2025-07-12", "route_name": "452SA", "details": {"duration_hours": 10, "type": "regular"}}
]

class RouteBackupManager:
    """Manages route backup and recovery operations"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    async def backup_current_routes(self) -> List[Dict[str, Any]]:
        """Create backup of current routes in the system"""
        try:
            async with self.db_manager.get_connection() as conn:
                routes = await conn.fetch("""
                    SELECT route_name, date, details, created_at
                    FROM routes 
                    WHERE date BETWEEN '2025-07-07' AND '2025-07-13'
                    ORDER BY date, route_name
                """)
                
                backup_data = []
                for route in routes:
                    backup_data.append({
                        "route_name": route['route_name'],
                        "date": route['date'].strftime('%Y-%m-%d'),
                        "details": route['details'],
                        "created_at": route['created_at'].isoformat() if route['created_at'] else None
                    })
                
                logger.info(f"Backed up {len(backup_data)} routes")
                return backup_data
                
        except Exception as e:
            logger.error(f"Failed to backup routes: {e}")
            return []
    
    async def restore_original_routes(self) -> bool:
        """Restore original system routes from backup with proper sequencing"""
        try:
            async with self.db_manager.get_connection() as conn:
                # First, clear existing routes for the week
                await conn.execute("""
                    DELETE FROM routes 
                    WHERE date BETWEEN '2025-07-07' AND '2025-07-13'
                """)
                logger.info("Cleared existing routes for July 7-13, 2025")
                
                # Restore original routes with proper route_id sequence (1-42)
                for idx, route_data in enumerate(ORIGINAL_ROUTES_BACKUP, 1):
                    route_date = datetime.strptime(route_data['date'], '%Y-%m-%d').date()
                    # Derive day_of_week from date
                    weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    day_of_week = weekday_names[route_date.weekday()]
                    
                    await conn.execute("""
                        INSERT INTO routes (route_id, date, route_name, day_of_week, details, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, 
                    idx,  # route_id starts from 1
                    route_date,
                    route_data['route_name'],
                    day_of_week,
                    json.dumps(route_data['details']),
                    datetime(2025, 8, 11, 21, 10, 0)  # Original system timestamp
                    )
                
                logger.info(f"Restored {len(ORIGINAL_ROUTES_BACKUP)} original routes")
                return True
                
        except Exception as e:
            logger.error(f"Failed to restore original routes: {e}")
            return False
    
    async def check_missing_routes(self) -> List[str]:
        """Check which original routes are missing from the system"""
        try:
            async with self.db_manager.get_connection() as conn:
                existing_routes = await conn.fetch("""
                    SELECT route_name, date 
                    FROM routes 
                    WHERE date BETWEEN '2025-07-07' AND '2025-07-13'
                """)
                
                existing_set = {(route['route_name'], route['date'].strftime('%Y-%m-%d')) 
                              for route in existing_routes}
                
                original_set = {(route['route_name'], route['date']) 
                              for route in ORIGINAL_ROUTES_BACKUP}
                
                missing_routes = original_set - existing_set
                missing_list = [f"{route_name} on {date}" for route_name, date in missing_routes]
                
                if missing_routes:
                    logger.warning(f"Missing {len(missing_routes)} original routes: {missing_list}")
                else:
                    logger.info("All original routes are present")
                
                return missing_list
                
        except Exception as e:
            logger.error(f"Failed to check missing routes: {e}")
            return []
    
    async def restore_missing_routes(self) -> int:
        """Restore only the missing original routes with proper sequencing"""
        try:
            missing_routes = await self.check_missing_routes()
            if not missing_routes:
                logger.info("No missing routes to restore")
                return 0
            
            restored_count = 0
            async with self.db_manager.get_connection() as conn:
                # Get the next available route_id 
                next_id = await conn.fetchval("SELECT COALESCE(MAX(route_id), 0) + 1 FROM routes")
                
                for route_data in ORIGINAL_ROUTES_BACKUP:
                    route_key = f"{route_data['route_name']} on {route_data['date']}"
                    if route_key in missing_routes:
                        route_date = datetime.strptime(route_data['date'], '%Y-%m-%d').date()
                        # Derive day_of_week from date
                        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        day_of_week = weekday_names[route_date.weekday()]
                        
                        await conn.execute("""
                            INSERT INTO routes (route_id, date, route_name, day_of_week, details, created_at)
                            VALUES ($1, $2, $3, $4, $5, $6)
                        """, 
                        next_id,
                        route_date,
                        route_data['route_name'],
                        day_of_week,
                        json.dumps(route_data['details']),
                        datetime(2025, 8, 11, 21, 10, 0)  # Original system timestamp
                        )
                        restored_count += 1
                        next_id += 1
            
            logger.info(f"Restored {restored_count} missing routes")
            return restored_count
            
        except Exception as e:
            logger.error(f"Failed to restore missing routes: {e}")
            return 0
    
    async def restore_default_fixed_assignments(self) -> int:
        """Clear all fixed assignments and restore default ones"""
        try:
            async with self.db_manager.get_connection() as conn:
                # Clear all existing fixed assignments
                await conn.execute("DELETE FROM fixed_assignments")
                logger.info("Cleared all existing fixed assignments")
                
                # Restore default fixed assignments
                restored_count = 0
                for assignment in DEFAULT_FIXED_ASSIGNMENTS:
                    await conn.execute("""
                        INSERT INTO fixed_assignments (driver_id, route_id, date)
                        VALUES ($1, $2, $3)
                    """, 
                    assignment['driver_id'],
                    assignment['route_id'],
                    datetime.strptime(assignment['date'], '%Y-%m-%d').date()
                    )
                    restored_count += 1
                
                logger.info(f"Restored {restored_count} default fixed assignments")
                return restored_count
                
        except Exception as e:
            logger.error(f"Failed to restore default fixed assignments: {e}")
            return 0