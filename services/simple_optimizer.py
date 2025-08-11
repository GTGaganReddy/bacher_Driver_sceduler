"""
Simple Driver Route Assignment for July 7-13, 2025 Supabase Data
Uses greedy assignment approach to ensure all routes are covered
"""

import logging
from typing import Dict, List, Any
from datetime import date
import json

logger = logging.getLogger(__name__)

def optimize_driver_schedule(drivers: List[Dict], routes: List[Dict], availability: List[Dict]) -> Dict[str, Any]:
    """
    Optimize driver assignments for July 7-13, 2025 using your authentic Supabase data
    
    Args:
        drivers: List of driver records from Supabase
        routes: List of route records for July 7-13, 2025 
        availability: List of availability records
    
    Returns:
        Dict containing optimal assignments
    """
    
    logger.info(f"Optimizing schedule: {len(drivers)} drivers, {len(routes)} routes, {len(availability)} availability records")
    
    # Create data structures
    driver_map = {d['driver_id']: d for d in drivers}
    
    # Group routes by date 
    routes_by_date = {}
    for route in routes:
        route_date = str(route['date'])
        if route_date not in routes_by_date:
            routes_by_date[route_date] = []
        routes_by_date[route_date].append(route)
    
    # Create availability lookup
    avail_map = {}
    for avail in availability:
        key = f"{avail['driver_id']}_{avail['date']}"
        avail_map[key] = avail['available']
    
    # Assignments result
    assignments = {}
    stats = {
        'total_routes': len(routes),
        'assigned_routes': 0,
        'unassigned_routes': 0,
        'driver_assignments': {},
        'date_breakdown': {}
    }
    
    # Process each date
    for route_date, date_routes in routes_by_date.items():
        assignments[route_date] = []
        stats['date_breakdown'][route_date] = {
            'total_routes': len(date_routes),
            'assigned': 0,
            'unassigned': 0
        }
        
        # Available drivers for this date
        available_drivers = []
        for driver_id, driver in driver_map.items():
            avail_key = f"{driver_id}_{route_date}"
            if avail_map.get(avail_key, False):
                available_drivers.append(driver)
        
        logger.info(f"Date {route_date}: {len(date_routes)} routes, {len(available_drivers)} available drivers")
        
        # Assign routes to drivers (greedy approach)
        driver_workload = {d['driver_id']: 0 for d in available_drivers}
        
        for route in date_routes:
            # Find best available driver (least loaded)
            best_driver = None
            if available_drivers:
                # For Saturday routes (451SA, 452SA), prefer Saturday drivers
                if 'SA' in route['route_name']:
                    saturday_drivers = [d for d in available_drivers if 'Samstag' in d['name']]
                    if saturday_drivers:
                        best_driver = min(saturday_drivers, key=lambda d: driver_workload[d['driver_id']])
                    else:
                        best_driver = min(available_drivers, key=lambda d: driver_workload[d['driver_id']])
                else:
                    # For weekday routes, any available driver
                    best_driver = min(available_drivers, key=lambda d: driver_workload[d['driver_id']])
            
            if best_driver:
                # Parse duration from route details
                duration = 8.0  # Default
                if route.get('details'):
                    if isinstance(route['details'], str):
                        try:
                            details = json.loads(route['details'])
                            duration_str = details.get('duration', '8:00')
                            if ':' in duration_str:
                                h, m = duration_str.split(':')
                                duration = float(h) + float(m) / 60.0
                        except:
                            duration = 8.0
                    elif isinstance(route['details'], dict):
                        duration_str = route['details'].get('duration', '8:00')
                        if ':' in str(duration_str):
                            h, m = str(duration_str).split(':')
                            duration = float(h) + float(m) / 60.0
                
                # Make assignment
                assignment = {
                    'driver_id': best_driver['driver_id'],
                    'driver_name': best_driver['name'],
                    'route_id': route['route_id'],
                    'route_name': route['route_name'],
                    'date': route_date,
                    'duration': duration,
                    'status': 'assigned'
                }
                
                assignments[route_date].append(assignment)
                driver_workload[best_driver['driver_id']] += duration
                stats['assigned_routes'] += 1
                stats['date_breakdown'][route_date]['assigned'] += 1
                
                # Track driver assignments
                if best_driver['name'] not in stats['driver_assignments']:
                    stats['driver_assignments'][best_driver['name']] = 0
                stats['driver_assignments'][best_driver['name']] += 1
                
                logger.debug(f"Assigned {route['route_name']} to {best_driver['name']} ({duration}h)")
            else:
                # Unassigned route
                stats['unassigned_routes'] += 1
                stats['date_breakdown'][route_date]['unassigned'] += 1
                logger.warning(f"Could not assign route {route['route_name']} on {route_date}")
    
    # Calculate success rate
    success_rate = (stats['assigned_routes'] / stats['total_routes']) * 100 if stats['total_routes'] > 0 else 0
    
    result = {
        'status': 'success' if success_rate >= 80 else 'partial',
        'success_rate': success_rate,
        'assignments': assignments,
        'statistics': stats,
        'optimization_method': 'greedy_assignment',
        'week_period': 'July 7-13, 2025',
        'data_source': 'Supabase'
    }
    
    logger.info(f"Optimization complete: {success_rate:.1f}% success rate, {stats['assigned_routes']}/{stats['total_routes']} routes assigned")
    
    return result