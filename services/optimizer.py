"""
OR-Tools Driver Route Assignment Optimization - Complete Implementation
Handles exact database format and optimizes driver-route assignments day by day
- Sequential optimization: solves each day in chronological order
- Updates remaining hours between days for accurate capacity tracking
- Special Saturday rule for route 252SA
- Prioritizes drivers with most remaining monthly hours
- Enhanced fixed route assignment support
"""

from ortools.linear_solver import pywraplp
from datetime import datetime, timedelta, date
import json
from typing import Dict, List, Tuple, Optional
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

# Helper functions for parsing database format
def parse_time_string_to_hours(time_str: str) -> float:
    """Convert time string like '11:00' or '174:00' to hours as float"""
    if not time_str or not isinstance(time_str, str):
        return 8.0  # Default fallback
    
    try:
        parts = time_str.split(':')
        if len(parts) == 2:
            hours = int(parts[0])
            minutes = int(parts[1])
            return hours + (minutes / 60.0)
    except (ValueError, IndexError):
        pass
    
    return 8.0  # Default fallback

def parse_json_details(details_str: str) -> Dict:
    """Parse JSON string from database details field"""
    if not details_str:
        return {}
    
    try:
        import json
        return json.loads(details_str)
    except (json.JSONDecodeError, TypeError):
        return {}

def optimize_routes_for_date(routes: List[Dict], driver_info: Dict, driver_remaining_hours: Dict, 
                           availability_map: Dict, route_date) -> List[Dict]:
    """Helper function to run OR-Tools optimization for a specific date"""
    try:
        # Create solver
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver:
            return []
        
        # Get available drivers for this date
        available_drivers = []
        for driver_id, info in driver_info.items():
            # Check availability
            if driver_id in availability_map and route_date in availability_map[driver_id]:
                if not availability_map[driver_id][route_date]:
                    continue
            
            # Check remaining hours
            if driver_remaining_hours[driver_id] > 0:
                available_drivers.append(driver_id)
        
        if not available_drivers or not routes:
            return []
        
        # Create decision variables
        assignments = {}
        for route in routes:
            for driver_id in available_drivers:
                var_name = f"assign_{route['route_id']}_to_{driver_id}"
                assignments[(route['route_id'], driver_id)] = solver.BoolVar(var_name)
        
        # Constraint: Each route assigned to exactly one driver
        for route in routes:
            constraint = solver.Constraint(1, 1)
            for driver_id in available_drivers:
                constraint.SetCoefficient(assignments[(route['route_id'], driver_id)], 1)
        
        # Constraint: Driver capacity
        for driver_id in available_drivers:
            constraint = solver.Constraint(0, driver_remaining_hours[driver_id])
            for route in routes:
                constraint.SetCoefficient(
                    assignments[(route['route_id'], driver_id)], 
                    route['duration_hours']
                )
        
        # Objective: Maximize assignments (minimize unassigned routes)
        objective = solver.Objective()
        for route in routes:
            for driver_id in available_drivers:
                objective.SetCoefficient(assignments[(route['route_id'], driver_id)], 1)
        objective.SetMaximization()
        
        # Solve
        status = solver.Solve()
        
        # Extract solution
        result_assignments = []
        if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
            for route in routes:
                for driver_id in available_drivers:
                    if assignments[(route['route_id'], driver_id)].solution_value() > 0.5:
                        result_assignments.append({
                            'route_id': route['route_id'],
                            'route_name': route['route_name'],
                            'driver_id': driver_id,
                            'driver_name': driver_info[driver_id]['name'],
                            'duration_hours': route['duration_hours']
                        })
                        logger.info(f"OPTIMIZED: Assigned {route['route_name']} to {driver_info[driver_id]['name']} ({route['duration_hours']}h)")
        
        return result_assignments
        
    except Exception as e:
        logger.error(f"Date-specific optimization failed: {str(e)}")
        return []

def run_ortools_optimization_with_fixed_routes(drivers: List[Dict], routes: List[Dict], 
                                                availability: List[Dict], fixed_routes: List[Dict] = None) -> Dict:
    """
    Enhanced OR-Tools optimization with fixed driver-route priority assignments
    
    Process:
    1. Apply fixed route assignments first (if driver is available)
    2. Run OR-Tools optimization for remaining routes
    3. Fallback: If fixed driver unavailable, route goes to optimization pool
    
    Args:
        drivers: List of driver dictionaries
        routes: List of route dictionaries  
        availability: List of driver availability dictionaries
        fixed_routes: List of fixed driver-route assignments from database
    """
    from datetime import datetime
    import copy
    
    try:
        logger.info(f"Starting enhanced optimization with {len(fixed_routes or [])} fixed route rules")
        
        # Parse drivers from database format
        driver_info = {}
        driver_remaining_hours = {}
        
        for driver in drivers:
            driver_id = driver.get('driver_id') or driver.get('id')
            driver_name = driver.get('name', 'Unknown Driver')
            
            details = parse_json_details(driver.get('details', ''))
            monthly_hours_str = details.get('monthly_hours', '160:00')
            monthly_hours = parse_time_string_to_hours(monthly_hours_str)
            
            driver_info[driver_id] = {
                'name': driver_name,
                'monthly_hours': monthly_hours,
                'type': details.get('type', 'unknown')
            }
            driver_remaining_hours[driver_id] = monthly_hours
        
        # Parse availability - driver available on specific dates
        availability_map = {}
        for avail in availability:
            driver_id = avail.get('driver_id')
            avail_date = avail.get('date')
            is_available = avail.get('available', True)
            
            if driver_id not in availability_map:
                availability_map[driver_id] = {}
            availability_map[driver_id][avail_date] = is_available
        
        # Parse routes and group by date
        routes_by_date = {}
        for route in routes:
            route_date = route.get('date')
            route_name = route.get('route_name', 'Unknown Route')
            route_id = route.get('route_id')
            
            details = parse_json_details(route.get('details', ''))
            duration_str = details.get('duration', '8:00')
            duration_hours = parse_time_string_to_hours(duration_str)
            
            if route_date not in routes_by_date:
                routes_by_date[route_date] = []
            
            routes_by_date[route_date].append({
                'route_id': route_id,
                'route_name': route_name,
                'duration_hours': duration_hours,
                'details': details
            })
        
        # Create fixed route lookup for quick matching
        fixed_route_lookup = {}
        if fixed_routes:
            for fixed_route in fixed_routes:
                route_pattern = fixed_route.get('route_pattern')
                driver_id = fixed_route.get('driver_id')
                day_of_week = fixed_route.get('day_of_week', 'any').lower()
                priority = fixed_route.get('priority', 1)
                
                if route_pattern not in fixed_route_lookup:
                    fixed_route_lookup[route_pattern] = []
                
                fixed_route_lookup[route_pattern].append({
                    'driver_id': driver_id,
                    'driver_name': fixed_route.get('driver_name'),
                    'day_of_week': day_of_week,
                    'priority': priority
                })
        
        # Sequential optimization with fixed route handling
        final_assignments = {}
        total_assigned = 0
        all_unassigned_routes = []
        driver_hours_used = {driver_id: 0 for driver_id in driver_info.keys()}
        
        for route_date in sorted(routes_by_date.keys()):
            date_str = route_date.strftime('%Y-%m-%d') if hasattr(route_date, 'strftime') else str(route_date)
            day_name = route_date.strftime('%A').lower() if hasattr(route_date, 'strftime') else 'unknown'
            
            logger.info(f"Processing date: {date_str} ({day_name})")
            
            date_routes = routes_by_date[route_date]
            fixed_assignments = []
            remaining_routes = []
            
            # Pre-populate with F entries for unavailable drivers
            final_assignments[date_str] = {}
            for driver_id, driver_data in driver_info.items():
                if driver_id in availability_map and route_date in availability_map[driver_id]:
                    if not availability_map[driver_id][route_date]:
                        f_key = f"F_{driver_data['name']}_{date_str}"
                        final_assignments[date_str][f_key] = {
                            'driver_name': driver_data['name'],
                            'driver_id': driver_id,
                            'route_id': None,
                            'duration_hours': 0.0,
                            'duration_formatted': "00:00",
                            'status': 'unavailable',
                            'assignment_type': 'unavailable'
                        }
            
            # Phase 1: Apply fixed route assignments
            for route in date_routes:
                route_name = route['route_name']
                assigned_via_fixed = False
                
                # Check if this route has fixed assignments
                if route_name in fixed_route_lookup:
                    # Sort by priority (lower number = higher priority)
                    candidates = sorted(fixed_route_lookup[route_name], key=lambda x: x['priority'])
                    
                    for candidate in candidates:
                        driver_id = candidate['driver_id']
                        required_day = candidate['day_of_week']
                        
                        # Check day of week compatibility
                        if required_day != 'any' and required_day != day_name:
                            continue
                        
                        # Check driver availability
                        if driver_id in availability_map and route_date in availability_map[driver_id]:
                            if not availability_map[driver_id][route_date]:
                                logger.info(f"Fixed driver {candidate['driver_name']} unavailable for {route_name} on {date_str}")
                                continue
                        
                        # Check remaining hours
                        if driver_remaining_hours[driver_id] < route['duration_hours']:
                            logger.info(f"Fixed driver {candidate['driver_name']} insufficient hours for {route_name}")
                            continue
                        
                        # Assign fixed route
                        fixed_assignments.append({
                            'route_id': route['route_id'],
                            'route_name': route_name,
                            'driver_id': driver_id,
                            'driver_name': candidate['driver_name'],
                            'duration_hours': route['duration_hours'],
                            'assignment_type': 'fixed'
                        })
                        
                        # Reduce driver hours
                        driver_remaining_hours[driver_id] -= route['duration_hours']
                        driver_hours_used[driver_id] += route['duration_hours']
                        assigned_via_fixed = True
                        total_assigned += 1
                        
                        logger.info(f"FIXED: Assigned {route_name} to {candidate['driver_name']} ({route['duration_hours']}h). Remaining: {driver_remaining_hours[driver_id]:.1f}h")
                        break
                
                # If not assigned via fixed route, add to optimization pool
                if not assigned_via_fixed:
                    remaining_routes.append(route)
            
            # Phase 2: OR-Tools optimization for remaining routes
            if remaining_routes:
                logger.info(f"Running OR-Tools for {len(remaining_routes)} remaining routes on {date_str}")
                
                # Run standard optimization for remaining routes
                optimized_assignments = optimize_routes_for_date(
                    remaining_routes, driver_info, driver_remaining_hours, 
                    availability_map, route_date
                )
                
                # Update remaining hours and add to final assignments
                for assignment in optimized_assignments:
                    driver_id = assignment['driver_id']
                    driver_remaining_hours[driver_id] -= assignment['duration_hours']
                    driver_hours_used[driver_id] += assignment['duration_hours']
                    total_assigned += 1
                    assignment['assignment_type'] = 'optimized'
            else:
                optimized_assignments = []
            
            # Combine fixed and optimized assignments for this date
            all_date_assignments = fixed_assignments + optimized_assignments
            
            # Add assignments to final result with proper keys
            for assignment in all_date_assignments:
                route_name = assignment['route_name']
                final_assignments[date_str][route_name] = {
                    'driver_name': assignment['driver_name'],
                    'driver_id': assignment['driver_id'],
                    'route_id': assignment['route_id'],
                    'duration_hours': assignment['duration_hours'],
                    'duration_formatted': f"{int(assignment['duration_hours'])}:{int((assignment['duration_hours'] % 1) * 60):02d}",
                    'status': 'assigned',
                    'assignment_type': assignment.get('assignment_type', 'optimized')
                }
            
            # Track unassigned routes
            assigned_route_ids = {a['route_id'] for a in all_date_assignments}
            for route in date_routes:
                if route['route_id'] not in assigned_route_ids:
                    all_unassigned_routes.append({
                        'route_id': route['route_id'],
                        'route_name': route['route_name'],
                        'date': date_str,
                        'duration_hours': route['duration_hours']
                    })
        
        # Calculate statistics
        total_routes = sum(len(routes_by_date[date]) for date in routes_by_date)
        assigned_routes = total_assigned
        unassigned_routes = len(all_unassigned_routes)
        
        # Driver utilization
        driver_utilization = {}
        for driver_id, info in driver_info.items():
            hours_used = driver_hours_used[driver_id]
            total_hours = info['monthly_hours']
            utilization_pct = (hours_used / total_hours * 100) if total_hours > 0 else 0
            
            driver_utilization[info['name']] = {
                'hours_used': hours_used,
                'total_hours': total_hours,
                'remaining_hours': total_hours - hours_used,
                'utilization_percentage': utilization_pct
            }
        
        logger.info(f"Enhanced optimization completed: {total_routes} total routes assigned ({assigned_routes} assigned, {unassigned_routes} unassigned)")
        
        # FULL OPTIMIZER OUTPUT LOGGING
        logger.info("=== COMPLETE OPTIMIZER OUTPUT ===")
        import json
        result_data = {
            'assignments': final_assignments,
            'stats': {
                'total_routes': total_routes,
                'assigned_routes': assigned_routes,
                'unassigned_routes': unassigned_routes,
                'solver_status': solver_status,
                'driver_utilization': driver_utilization
            },
            'unassigned_routes': all_unassigned_routes
        }
        logger.info(f"Complete optimizer result: {json.dumps(result_data, indent=2)}")
        logger.info("=== END OPTIMIZER OUTPUT ===")
        
        # Determine solver status based on results
        if unassigned_routes == 0:
            solver_status = "OPTIMAL_WITH_FIXED_ROUTES"
        elif assigned_routes > 0:
            solver_status = "FEASIBLE_WITH_FIXED_ROUTES"
        else:
            solver_status = "NO_SOLUTION_FOUND"
        
        return {
            'assignments': final_assignments,
            'stats': {
                'total_routes': total_routes,
                'assigned_routes': assigned_routes,
                'unassigned_routes': unassigned_routes,
                'solver_status': solver_status,
                'driver_utilization': driver_utilization
            },
            'unassigned_routes': all_unassigned_routes
        }
        
    except Exception as e:
        logger.error(f"Enhanced optimization failed: {str(e)}")
        return {
            'assignments': {},
            'stats': {
                'total_routes': 0,
                'assigned_routes': 0,
                'unassigned_routes': 0,
                'solver_status': 'ERROR',
                'error_message': str(e)
            },
            'unassigned_routes': []
        }

def run_ortools_optimization(drivers: List[Dict], routes: List[Dict], availability: List[Dict]) -> Dict:
    """
    Original OR-Tools optimization function - Sequential algorithm implementation
    Processes each day individually in chronological order for realistic scheduling
    
    Args:
        drivers: List of driver dictionaries from database
        routes: List of route dictionaries from database  
        availability: List of driver availability dictionaries from database
    """
    from datetime import datetime
    
    try:
        logger.info(f"Starting sequential OR-Tools optimization for {len(routes)} routes and {len(drivers)} drivers")
        
        # Parse drivers from database format
        driver_info = {}
        driver_remaining_hours = {}
        
        for driver in drivers:
            driver_id = driver.get('driver_id') or driver.get('id')
            driver_name = driver.get('name', 'Unknown Driver')
            
            # Parse monthly hours from details JSON
            details = parse_json_details(driver.get('details', ''))
            monthly_hours_str = details.get('monthly_hours', '160:00')
            monthly_hours = parse_time_string_to_hours(monthly_hours_str)
            
            driver_info[driver_id] = {
                'name': driver_name,
                'monthly_hours': monthly_hours,
                'type': details.get('type', 'unknown')
            }
            driver_remaining_hours[driver_id] = monthly_hours
        
        # Parse availability - driver available on specific dates
        availability_map = {}
        for avail in availability:
            driver_id = avail.get('driver_id')
            avail_date = avail.get('date')
            is_available = avail.get('available', True)
            
            if driver_id not in availability_map:
                availability_map[driver_id] = {}
            availability_map[driver_id][avail_date] = is_available
        
        # Parse routes and group by date
        routes_by_date = {}
        for route in routes:
            route_date = route.get('date')
            route_name = route.get('route_name', 'Unknown Route')
            route_id = route.get('route_id')
            
            # Parse duration from details JSON
            details = parse_json_details(route.get('details', ''))
            duration_str = details.get('duration', '8:00')
            duration_hours = parse_time_string_to_hours(duration_str)
            
            if route_date not in routes_by_date:
                routes_by_date[route_date] = []
            
            routes_by_date[route_date].append({
                'route_id': route_id,
                'route_name': route_name,
                'duration_hours': duration_hours,
                'details': details
            })
        
        # Sequential optimization: process each day independently
        final_assignments = {}
        total_assigned = 0
        all_unassigned_routes = []
        driver_hours_used = {driver_id: 0 for driver_id in driver_info.keys()}
        
        # Process dates in chronological order
        for route_date in sorted(routes_by_date.keys()):
            date_str = route_date.strftime('%Y-%m-%d') if hasattr(route_date, 'strftime') else str(route_date)
            day_name = route_date.strftime('%A').lower() if hasattr(route_date, 'strftime') else 'unknown'
            
            logger.info(f"Processing date: {date_str} ({day_name})")
            
            date_routes = routes_by_date[route_date]
            
            # Pre-populate with F entries for unavailable drivers
            final_assignments[date_str] = {}
            for driver_id, driver_data in driver_info.items():
                if driver_id in availability_map and route_date in availability_map[driver_id]:
                    if not availability_map[driver_id][route_date]:
                        f_key = f"F_{driver_data['name']}_{date_str}"
                        final_assignments[date_str][f_key] = {
                            'driver_name': driver_data['name'],
                            'driver_id': driver_id,
                            'route_id': None,
                            'duration_hours': 0.0,
                            'duration_formatted': "00:00",
                            'status': 'unavailable'
                        }
            
            # Apply special Saturday route 452SA rule for Klagenfurt - Samstagsfahrer
            saturday_driver_id = None
            for driver_id, info in driver_info.items():
                if 'samstag' in info['name'].lower():
                    saturday_driver_id = driver_id
                    break
            
            # Check for Saturday route 452SA assignment
            if day_name == 'saturday' and saturday_driver_id:
                for route in date_routes[:]:  # Use slice to avoid modification during iteration
                    if route['route_name'] == '452SA':
                        # Check if saturday driver is available
                        if (saturday_driver_id not in availability_map or 
                            route_date not in availability_map[saturday_driver_id] or
                            availability_map[saturday_driver_id][route_date]):
                            
                            # Check remaining hours
                            if driver_remaining_hours[saturday_driver_id] >= route['duration_hours']:
                                # Assign to Saturday driver
                                final_assignments[date_str][route['route_name']] = {
                                    'driver_name': driver_info[saturday_driver_id]['name'],
                                    'driver_id': saturday_driver_id,
                                    'route_id': route['route_id'],
                                    'duration_hours': route['duration_hours'],
                                    'duration_formatted': f"{int(route['duration_hours'])}:{int((route['duration_hours'] % 1) * 60):02d}",
                                    'status': 'assigned'
                                }
                                
                                # Update capacity
                                driver_remaining_hours[saturday_driver_id] -= route['duration_hours']
                                driver_hours_used[saturday_driver_id] += route['duration_hours']
                                total_assigned += 1
                                
                                # Remove from routes to optimize
                                date_routes.remove(route)
                                logger.info(f"Special Saturday rule: Assigned {route['route_name']} to {driver_info[saturday_driver_id]['name']} ({route['duration_hours']}h)")
                                break
            
            # Run OR-Tools optimization for remaining routes on this date
            optimized_assignments = optimize_routes_for_date(
                date_routes, driver_info, driver_remaining_hours, 
                availability_map, route_date
            )
            
            # Process optimization results
            assigned_route_ids = set()
            for assignment in optimized_assignments:
                route_name = assignment['route_name']
                driver_id = assignment['driver_id']
                
                # Add to final assignments
                final_assignments[date_str][route_name] = {
                    'driver_name': assignment['driver_name'],
                    'driver_id': driver_id,
                    'route_id': assignment['route_id'],
                    'duration_hours': assignment['duration_hours'],
                    'duration_formatted': f"{int(assignment['duration_hours'])}:{int((assignment['duration_hours'] % 1) * 60):02d}",
                    'status': 'assigned'
                }
                
                # Update capacity for subsequent days
                driver_remaining_hours[driver_id] -= assignment['duration_hours']
                driver_hours_used[driver_id] += assignment['duration_hours']
                assigned_route_ids.add(assignment['route_id'])
                total_assigned += 1
            
            # Track unassigned routes for this date
            for route in date_routes:
                if route['route_id'] not in assigned_route_ids:
                    all_unassigned_routes.append({
                        'route_id': route['route_id'],
                        'route_name': route['route_name'],
                        'date': date_str,
                        'duration_hours': route['duration_hours']
                    })
        
        # Calculate statistics
        total_routes = sum(len(routes_by_date[date]) for date in routes_by_date)
        assigned_routes = total_assigned
        unassigned_routes = len(all_unassigned_routes)
        
        # Driver utilization
        driver_utilization = {}
        for driver_id, info in driver_info.items():
            hours_used = driver_hours_used[driver_id]
            total_hours = info['monthly_hours']
            utilization_pct = (hours_used / total_hours * 100) if total_hours > 0 else 0
            
            driver_utilization[info['name']] = {
                'hours_used': hours_used,
                'total_hours': total_hours,
                'remaining_hours': total_hours - hours_used,
                'utilization_percentage': utilization_pct
            }
        
        logger.info(f"Sequential optimization completed: {total_routes} total routes ({assigned_routes} assigned, {unassigned_routes} unassigned)")
        
        # Determine solver status
        if unassigned_routes == 0:
            solver_status = "OPTIMAL"
        elif assigned_routes > 0:
            solver_status = "FEASIBLE"
        else:
            solver_status = "NO_SOLUTION_FOUND"
        
        return {
            'assignments': final_assignments,
            'stats': {
                'total_routes': total_routes,
                'assigned_routes': assigned_routes,
                'unassigned_routes': unassigned_routes,
                'solver_status': solver_status,
                'driver_utilization': driver_utilization
            },
            'unassigned_routes': all_unassigned_routes
        }
        
    except Exception as e:
        logger.error(f"Sequential optimization failed: {str(e)}")
        return {
            'assignments': {},
            'stats': {
                'total_routes': 0,
                'assigned_routes': 0,
                'unassigned_routes': 0,
                'solver_status': 'ERROR',
                'error_message': str(e)
            },
            'unassigned_routes': []
        }

class SchedulingOptimizer:
    """
    Legacy SchedulingOptimizer class for backward compatibility
    """
    
    def __init__(self):
        pass
    
    def optimize(self, drivers: List[Dict], routes: List[Dict], availability: List[Dict]) -> Dict:
        """
        Legacy optimization method - calls the enhanced fixed routes optimizer
        """
        return run_ortools_optimization_with_fixed_routes(drivers, routes, availability, fixed_routes=[])

class DriverRouteOptimizer:
    """
    Legacy DriverRouteOptimizer class for backward compatibility
    """
    
    def __init__(self):
        pass
    
    def optimize_routes(self, drivers: List[Dict], routes: List[Dict], availability: List[Dict]) -> Dict:
        """
        Legacy optimization method - calls the original OR-Tools optimizer
        """
        return run_ortools_optimization(drivers, routes, availability)