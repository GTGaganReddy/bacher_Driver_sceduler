from fastapi import Depends
from database.connection import DatabaseManager
from services.database import DatabaseService
from services.optimizer import SchedulingOptimizer
from services.google_sheets import GoogleSheetsService

# Create a global database manager instance
db_manager = DatabaseManager()

def get_database_service() -> DatabaseService:
    """Dependency to get database service instance"""
    return DatabaseService(db_manager)

def get_scheduling_optimizer() -> SchedulingOptimizer:
    """Dependency to get scheduling optimizer instance"""
    return SchedulingOptimizer()

def get_google_sheets_service() -> GoogleSheetsService:
    """Dependency to get Google Sheets service instance"""
    return GoogleSheetsService()
