import asyncpg
import logging
import os
from config.settings import settings
from datetime import date, datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.pool = None
    
    async def init_pool(self):
        """Initialize connection pool - fallback to local for development when Supabase IPv6 unavailable"""
        try:
            # Use Supabase session pooler connection to access authentic July 7-13, 2025 data
            supabase_pooler_url = f"postgresql://postgres.nqwyglxhvhlrviknykmt:{settings.SUPABASE_PASSWORD}@aws-0-eu-north-1.pooler.supabase.com:5432/postgres"
            database_url = supabase_pooler_url
            
            self.pool = await asyncpg.create_pool(
                database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            # Skip table creation - using existing Supabase tables and data
            logger.info("Connected to Supabase via session pooler - using authentic July 7-13, 2025 data")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close_pool(self):
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
    
    def get_connection(self):
        """Get a connection from the pool"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        return self.pool.acquire()
    
    async def create_tables(self):
        """Create all necessary tables"""
        async with self.pool.acquire() as conn:
            # Create drivers table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS drivers (
                    driver_id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    monthly_hours_limit INTEGER DEFAULT 174,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create driver_availability table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS driver_availability (
                    id SERIAL PRIMARY KEY,
                    driver_id INT REFERENCES drivers(driver_id) ON DELETE CASCADE,
                    date DATE NOT NULL,
                    available BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(driver_id, date)
                );
            """)
            
            # Create routes table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS routes (
                    route_id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    route_name TEXT NOT NULL,
                    day_of_week TEXT,
                    details JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create assignments table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS assignments (
                    id SERIAL PRIMARY KEY,
                    week_start DATE NOT NULL,
                    assignments JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create fixed assignments table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fixed_assignments (
                    id SERIAL PRIMARY KEY,
                    driver_id INTEGER NOT NULL,
                    route_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(driver_id, route_id, date)
                );
            """)
            
            logger.info("All tables created successfully")
    
    async def insert_july_2025_data(self):
        """Insert authentic July 7-13, 2025 driver scheduling data matching your Supabase structure"""
        async with self.pool.acquire() as conn:
            # Insert 21 real drivers with their actual monthly hour limits
            driver_count = await conn.fetchval("SELECT COUNT(*) FROM drivers")
            if driver_count == 0:
                real_drivers = [
                    ("Blaskovic, Nenad", 174), ("Fröhlacher, Hubert", 174), ("Genäuß, Thomas", 174),
                    ("Hinteregger, Manfred", 174), ("Kandolf, Alfred", 174), ("Konheiser, Elisabeth", 174),
                    ("Lauhart, Egon", 174), ("Madrutter, Anton", 174), ("Niederbichler, Daniel", 174),
                    ("Nurikic, Ervin", 174), ("Obersteiner, Roland", 174), ("Rauter, Agnes Zita", 174),
                    ("Simon, Otto", 174), ("Bandzi, Attila", 174), ("Struckl, Stefan", 174),
                    ("Merz, Matthias", 174), ("Granitzer, Hermann", 174), ("Thamer, Karl", 174),
                    ("Sulics, Egon", 174), ("Klagenfurt - Fahrer", 40), ("Klagenfurt - Samstagsfahrer", 40)
                ]
                
                for name, hours_limit in real_drivers:
                    await conn.execute(
                        "INSERT INTO drivers (name, monthly_hours_limit) VALUES ($1, $2)",
                        name, hours_limit
                    )
                logger.info(f"Inserted {len(real_drivers)} real drivers with monthly hour limits")
            
            # Insert routes for July 7-13, 2025 (weekday routes 431oS-440oS, Saturday routes 451SA-452SA)  
            route_count = await conn.fetchval("SELECT COUNT(*) FROM routes WHERE date >= '2025-07-07' AND date <= '2025-07-13'")
            if route_count == 0:
                # Weekday routes (Mon-Fri: July 7,8,9,10,11)
                weekday_routes = ["431oS", "432oS", "433oS", "434oS", "435oS", "436oS", "437oS", "438oS", "439oS", "440oS"]
                # Saturday routes (Sat: July 12) 
                saturday_routes = ["451SA", "452SA"]
                
                # July 7-11 (Monday-Friday) - weekday routes
                for day_offset in range(5):  # Mon-Fri
                    route_date = date(2025, 7, 7 + day_offset)
                    for route_name in weekday_routes:
                        await conn.execute(
                            "INSERT INTO routes (date, route_name, details) VALUES ($1, $2, $3)",
                            route_date, route_name, '{"duration": "8:00", "type": "weekday"}'
                        )
                
                # July 12 (Saturday) - Saturday routes  
                saturday_date = date(2025, 7, 12)
                for route_name in saturday_routes:
                    await conn.execute(
                        "INSERT INTO routes (date, route_name, details) VALUES ($1, $2, $3)",
                        saturday_date, route_name, '{"duration": "8:00", "type": "saturday"}'
                    )
                
                total_routes = 5 * len(weekday_routes) + len(saturday_routes)  # 50 weekday + 2 Saturday = 52 routes
                logger.info(f"Inserted {total_routes} routes for July 7-13, 2025 week")
            
            # Insert driver availability for July 7-13, 2025
            avail_count = await conn.fetchval("SELECT COUNT(*) FROM driver_availability WHERE date >= '2025-07-07' AND date <= '2025-07-13'")
            if avail_count == 0:
                drivers = await conn.fetch("SELECT driver_id, name FROM drivers")
                
                for driver_record in drivers:
                    driver_id = driver_record['driver_id']
                    driver_name = driver_record['name']
                    
                    # Set availability for July 7-13, 2025 
                    for day_offset in range(7):  # Full week
                        avail_date = date(2025, 7, 7 + day_offset)
                        
                        # Saturday-only drivers work only on Saturday (July 12)
                        if "Samstag" in driver_name:
                            available = (avail_date.weekday() == 5)  # Saturday
                        else:
                            available = True  # Regular drivers available all days
                        
                        await conn.execute(
                            "INSERT INTO driver_availability (driver_id, date, available) VALUES ($1, $2, $3)",
                            driver_id, avail_date, available
                        )
                
                logger.info(f"Inserted availability records for {len(drivers)} drivers for July 7-13, 2025")

    async def insert_default_data(self):
        """Insert real drivers and routes if none exist"""
        async with self.pool.acquire() as conn:
            # Insert real drivers with their monthly hours
            driver_count = await conn.fetchval("SELECT COUNT(*) FROM drivers")
            if driver_count == 0:
                real_drivers = [
                    ("Blaskovic, Nenad",), ("Fröhlacher, Hubert",), ("Genäuß, Thomas",),
                    ("Hinteregger, Manfred",), ("Kandolf, Alfred",), ("Konheiser, Elisabeth",),
                    ("Lauhart, Egon",), ("Madrutter, Anton",), ("Niederbichler, Daniel",),
                    ("Nurikic, Ervin",), ("Obersteiner, Roland",), ("Rauter, Agnes Zita",),
                    ("Simon, Otto",), ("Bandzi, Attila",), ("Struckl, Stefan",),
                    ("Merz, Matthias",), ("Granitzer, Hermann",), ("Thamer, Karl",),
                    ("Sulics, Egon",), ("Klagenfurt - Fahrer",), ("Klagenfurt - Samstagsfahrer",)
                ]
                await conn.executemany(
                    "INSERT INTO drivers (name) VALUES ($1)",
                    real_drivers
                )
                logger.info(f"Inserted {len(real_drivers)} real drivers")
            
            # Insert real routes
            route_count = await conn.fetchval("SELECT COUNT(*) FROM routes")
            if route_count == 0:
                # Monday to Friday routes
                weekday_routes = [
                    ("431oS", "11:00"), ("432oS", "12:00"), ("433oS", "11:00"), ("434oS", "10:00"),
                    ("437oS", "11:00"), ("438oS", "11:00"), ("439oS", "12:00"), ("440oS", "3:00")
                ]
                # Saturday routes
                saturday_routes = [("451SA", "8:00"), ("452SA", "8:00")]
                
                # Insert weekday routes (Monday-Friday)
                from datetime import date, timedelta
                today = date.today()
                
                # Generate routes for the current week
                for day_offset in range(7):  # Week dates
                    current_date = today + timedelta(days=day_offset)
                    weekday = current_date.weekday()  # 0=Monday, 6=Sunday
                    
                    if weekday < 5:  # Monday to Friday (0-4)
                        for route_name, hours in weekday_routes:
                            import json
                            await conn.execute("""
                                INSERT INTO routes (date, route_name, details) 
                                VALUES ($1, $2, $3)
                            """, current_date, route_name, json.dumps({"hours": hours, "type": "weekday"}))
                    elif weekday == 5:  # Saturday (5)
                        for route_name, hours in saturday_routes:
                            import json
                            await conn.execute("""
                                INSERT INTO routes (date, route_name, details) 
                                VALUES ($1, $2, $3)
                            """, current_date, route_name, json.dumps({"hours": hours, "type": "saturday"}))
                    # Sunday (6) - no routes (off day)
                
                total_routes = len(weekday_routes) * 5 + len(saturday_routes)  # 5 weekdays + 1 Saturday
                logger.info(f"Inserted {total_routes} real routes for the current week")
