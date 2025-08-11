import asyncpg
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.pool = None
    
    async def init_pool(self):
        """Initialize connection pool and create tables"""
        try:
            self.pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=2,
                max_size=10
            )
            await self.create_tables()
            await self.insert_default_data()
            logger.info("Database pool initialized successfully")
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
            
            logger.info("All tables created successfully")
    
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
