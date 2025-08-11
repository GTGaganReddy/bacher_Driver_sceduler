import os
from supabase import create_client, Client
from typing import List, Dict, Any, Optional
import logging
from datetime import date
from config.settings import settings

logger = logging.getLogger(__name__)

class SupabaseService:
    """
    Service for interacting with Supabase database using the Supabase client
    Provides all the CRUD operations mentioned in the API guide
    """
    
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self.client: Client = None
        
        if self.url and self.key:
            try:
                # Use updated credentials from user
                self.url = "https://nqwyglxhvhlrviknykmt.supabase.co"
                self.key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5xd3lnbHhodmhscnZpa255a210Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzQyMTk3OCwiZXhwIjoyMDY4OTk3OTc4fQ.xGolIcNOusVfqpfptE-uSo_eBaSYOx5QI-e9APiTOuA"
                self.client = create_client(self.url, self.key)
                logger.info("Supabase client initialized successfully with REST API")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.client = None
        else:
            logger.warning("Supabase credentials not provided, client not initialized")
    
    # Driver Availability Management
    async def update_driver_availability(self, driver_id: int, date: str, availability_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a single driver's availability for a specific date"""
        if not self.client:
            raise Exception("Supabase client not initialized")
        
        response = (self.client.table('driver_availability')
                   .update(availability_data)
                   .eq('driver_id', driver_id)
                   .eq('date', date)
                   .execute())
        return response.data
    
    async def batch_update_driver_availability(self, updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Update multiple drivers at once"""
        if not self.client:
            raise Exception("Supabase client not initialized")
        
        results = []
        for update in updates:
            driver_id = update.pop('driver_id')
            date = update.pop('date')
            
            response = (self.client.table('driver_availability')
                       .update(update)
                       .eq('driver_id', driver_id)
                       .eq('date', date)
                       .execute())
            results.append(response.data)
        
        return results
    
    async def create_availability_record(self, availability_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add availability for a new date"""
        if not self.client:
            raise Exception("Supabase client not initialized")
        
        response = (self.client.table('driver_availability')
                   .insert(availability_data)
                   .execute())
        return response.data
    
    async def get_driver_availability(self, date: str = None, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Get driver availability for a specific date or date range"""
        if not self.client:
            raise Exception("Supabase client not initialized")
        
        query = (self.client.table('driver_availability')
                .select('*, drivers(name, monthly_hours_limit)'))
        
        if date:
            query = query.eq('date', date).eq('available', True)
        elif start_date and end_date:
            query = query.gte('date', start_date).lte('date', end_date)
        
        response = query.order('date').execute()
        return response.data
    
    async def delete_availability_record(self, driver_id: int, date: str) -> Dict[str, Any]:
        """Remove availability record"""
        if not self.client:
            raise Exception("Supabase client not initialized")
        
        response = (self.client.table('driver_availability')
                   .delete()
                   .eq('driver_id', driver_id)
                   .eq('date', date)
                   .execute())
        return response.data
    
    # Route Management
    async def add_new_route(self, route_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a single new route"""
        if not self.client:
            raise Exception("Supabase client not initialized")
        
        response = (self.client.table('routes')
                   .insert(route_data)
                   .execute())
        return response.data
    
    async def batch_add_routes(self, routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add multiple routes at once"""
        if not self.client:
            raise Exception("Supabase client not initialized")
        
        response = (self.client.table('routes')
                   .insert(routes)
                   .execute())
        return response.data
    
    async def update_route(self, route_id: int, route_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update route details"""
        if not self.client:
            raise Exception("Supabase client not initialized")
        
        response = (self.client.table('routes')
                   .update(route_data)
                   .eq('route_id', route_id)
                   .execute())
        return response.data
    
    async def delete_route(self, route_id: int = None, date: str = None) -> Dict[str, Any]:
        """Delete a specific route or all routes for a specific date"""
        if not self.client:
            raise Exception("Supabase client not initialized")
        
        query = self.client.table('routes').delete()
        
        if route_id:
            query = query.eq('route_id', route_id)
        elif date:
            query = query.eq('date', date)
        else:
            raise ValueError("Either route_id or date must be provided")
        
        response = query.execute()
        return response.data
    
    async def get_routes(self, date: str = None, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Get routes for a specific date or date range"""
        if not self.client:
            raise Exception("Supabase client not initialized")
        
        query = self.client.table('routes').select('*')
        
        if date:
            query = query.eq('date', date)
        elif start_date and end_date:
            query = query.gte('date', start_date).lte('date', end_date)
        
        response = query.order('date').execute()
        return response.data
    
    # Advanced Queries
    async def get_available_drivers_for_scheduling(self, date: str) -> List[Dict[str, Any]]:
        """Get all available drivers for a specific date with their constraints"""
        if not self.client:
            raise Exception("Supabase client not initialized")
        
        response = (self.client.table('driver_availability')
                   .select('*, drivers(name, monthly_hours_limit)')
                   .eq('date', date)
                   .eq('available', True)
                   .order('available_hours', desc=True)
                   .execute())
        return response.data
    
    async def get_route_driver_compatibility(self, date: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get routes and available drivers for the same date"""
        if not self.client:
            raise Exception("Supabase client not initialized")
        
        routes_response = (self.client.table('routes')
                          .select('*')
                          .eq('date', date)
                          .execute())
        
        drivers_response = (self.client.table('driver_availability')
                           .select('*, drivers(name, monthly_hours_limit)')
                           .eq('date', date)
                           .eq('available', True)
                           .execute())
        
        return {
            'routes': routes_response.data,
            'available_drivers': drivers_response.data
        }
    
    # Utility Functions
    async def mark_driver_unavailable(self, driver_id: int, date: str, reason: str) -> Dict[str, Any]:
        """Mark driver unavailable for a specific date"""
        availability_data = {
            'available': False,
            'available_hours': 0,
            'max_routes': 0,
            'notes': reason
        }
        return await self.update_driver_availability(driver_id, date, availability_data)
    
    async def add_emergency_route(self, date: str, route_name: str, duration: str) -> Dict[str, Any]:
        """Add an emergency route"""
        import json
        from datetime import datetime
        
        day_of_week = datetime.strptime(date, '%Y-%m-%d').strftime('%A').lower()
        
        route_data = {
            'date': date,
            'route_name': route_name,
            'details': json.dumps({
                'duration': duration,
                'type': 'emergency',
                'route_code': route_name,
                'priority': 'high'
            })
        }
        
        return await self.add_new_route(route_data)
    
    # Real-time subscription setup helper
    def setup_realtime_subscriptions(self, callback_function):
        """Set up real-time subscriptions for database changes"""
        if not self.client:
            raise Exception("Supabase client not initialized")
        
        # Driver availability changes
        availability_subscription = (self.client.table('driver_availability')
                                    .on('*', callback_function)
                                    .subscribe())
        
        # Route changes
        route_subscription = (self.client.table('routes')
                             .on('*', callback_function)
                             .subscribe())
        
        return {
            'availability_subscription': availability_subscription,
            'route_subscription': route_subscription
        }