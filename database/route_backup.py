"""
Route Backup and Recovery System
Provides mechanisms to backup and restore original system routes
"""

from datetime import date, datetime
from typing import List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

# Original system routes for July 7-13, 2025 (42 routes)
ORIGINAL_ROUTES_BACKUP = [
    # Monday 2025-07-07 (6 routes)
    {"date": "2025-07-07", "route_name": "401MO", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-07", "route_name": "402MO", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-07", "route_name": "403MO", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-07", "route_name": "404MO", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-07", "route_name": "405MO", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-07", "route_name": "406MO", "details": {"duration_hours": 8, "type": "regular"}},
    
    # Tuesday 2025-07-08 (6 routes)
    {"date": "2025-07-08", "route_name": "411DI", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-08", "route_name": "412DI", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-08", "route_name": "413DI", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-08", "route_name": "414DI", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-08", "route_name": "415DI", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-08", "route_name": "416DI", "details": {"duration_hours": 8, "type": "regular"}},
    
    # Wednesday 2025-07-09 (6 routes)
    {"date": "2025-07-09", "route_name": "421MI", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-09", "route_name": "422MI", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-09", "route_name": "423MI", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-09", "route_name": "424MI", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-09", "route_name": "425MI", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-09", "route_name": "426MI", "details": {"duration_hours": 8, "type": "regular"}},
    
    # Thursday 2025-07-10 (6 routes)
    {"date": "2025-07-10", "route_name": "431DO", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-10", "route_name": "432DO", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-10", "route_name": "433DO", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-10", "route_name": "434DO", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-10", "route_name": "435DO", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-10", "route_name": "436DO", "details": {"duration_hours": 8, "type": "regular"}},
    
    # Friday 2025-07-11 (6 routes)
    {"date": "2025-07-11", "route_name": "441FR", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-11", "route_name": "442FR", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-11", "route_name": "443FR", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-11", "route_name": "444FR", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-11", "route_name": "445FR", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-11", "route_name": "446FR", "details": {"duration_hours": 8, "type": "regular"}},
    
    # Saturday 2025-07-12 (12 routes)
    {"date": "2025-07-12", "route_name": "451SA", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-12", "route_name": "452SA", "details": {"duration_hours": 8, "type": "special", "assigned_driver": "Klagenfurt - Samstagsfahrer"}},
    {"date": "2025-07-12", "route_name": "453SA", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-12", "route_name": "454SA", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-12", "route_name": "455SA", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-12", "route_name": "456SA", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-12", "route_name": "457SA", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-12", "route_name": "458SA", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-12", "route_name": "459SA", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-12", "route_name": "460SA", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-12", "route_name": "461SA", "details": {"duration_hours": 8, "type": "regular"}},
    {"date": "2025-07-12", "route_name": "462SA", "details": {"duration_hours": 8, "type": "regular"}}
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
        """Restore original system routes from backup"""
        try:
            async with self.db_manager.get_connection() as conn:
                # First, clear existing routes for the week
                await conn.execute("""
                    DELETE FROM routes 
                    WHERE date BETWEEN '2025-07-07' AND '2025-07-13'
                """)
                logger.info("Cleared existing routes for July 7-13, 2025")
                
                # Restore original routes
                for route_data in ORIGINAL_ROUTES_BACKUP:
                    await conn.execute("""
                        INSERT INTO routes (date, route_name, details, created_at)
                        VALUES ($1, $2, $3, $4)
                    """, 
                    datetime.strptime(route_data['date'], '%Y-%m-%d').date(),
                    route_data['route_name'],
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
        """Restore only the missing original routes"""
        try:
            missing_routes = await self.check_missing_routes()
            if not missing_routes:
                logger.info("No missing routes to restore")
                return 0
            
            restored_count = 0
            async with self.db_manager.get_connection() as conn:
                for route_data in ORIGINAL_ROUTES_BACKUP:
                    route_key = f"{route_data['route_name']} on {route_data['date']}"
                    if route_key in missing_routes:
                        await conn.execute("""
                            INSERT INTO routes (date, route_name, details, created_at)
                            VALUES ($1, $2, $3, $4)
                        """, 
                        datetime.strptime(route_data['date'], '%Y-%m-%d').date(),
                        route_data['route_name'],
                        json.dumps(route_data['details']),
                        datetime(2025, 8, 11, 21, 10, 0)  # Original system timestamp
                        )
                        restored_count += 1
            
            logger.info(f"Restored {restored_count} missing routes")
            return restored_count
            
        except Exception as e:
            logger.error(f"Failed to restore missing routes: {e}")
            return 0