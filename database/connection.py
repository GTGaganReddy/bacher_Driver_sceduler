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
        """Insert default drivers if none exist"""
        async with self.pool.acquire() as conn:
            driver_count = await conn.fetchval("SELECT COUNT(*) FROM drivers")
            if driver_count == 0:
                default_drivers = [
                    ("John Doe",), ("Jane Smith",), 
                    ("Bob Johnson",), ("Alice Brown",),
                    ("Mike Wilson",), ("Sarah Davis",)
                ]
                await conn.executemany(
                    "INSERT INTO drivers (name) VALUES ($1)",
                    default_drivers
                )
                logger.info(f"Inserted {len(default_drivers)} default drivers")
