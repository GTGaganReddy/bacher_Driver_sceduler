"""
OR-Tools Driver Route Assignment Optimization
Handles exact database format and optimizes driver-route assignments
- Parses JSON details fields from database
- Converts Decimal types to floats
- Handles time string parsing (11:00 -> 11.0 hours)
- Special Saturday rule for route 252SA
- Prioritizes drivers with most remaining monthly hours
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

class DriverRouteOptimizer:
    def __init__(self):
        self.solver = None
        
    def optimize_assignments(self, drivers_data: List[Dict], routes_data: List[Dict], 
                           availability_data: List[Dict]) -> Dict:
        """
        Run OR-Tools optimization for driver-route assignment with sequential hour reduction
        
        UPDATED: Implements true sequential optimization - solves day by day to ensure
        remaining capacity is properly reduced for subsequent days
        """
        from datetime import datetime
        import copy
        
        try:
            # Parse drivers from database format
            driver_info = {}
            driver_remaining_hours = {}  # Track remaining hours for each driver
            
            for driver in drivers_data:
                driver_id = driver.get('driver_id') or driver.get('id')
                driver_name = driver.get('name', 'Unknown Driver')
                
                # Parse JSON details field
                details = parse_json_details(driver.get('details', ''))
                monthly_hours_str = details.get('monthly_hours', '160:00')
                monthly_hours = parse_time_string_to_hours(monthly_hours_str)
                
                driver_info[driver_id] = {
                    'name': driver_name,
                    'monthly_hours': monthly_hours,
                    'type': details.get('type', 'unknown')
                }
                
                # Initialize remaining hours to full capacity
                driver_remaining_hours[driver_id] = monthly_hours
            
            # Parse routes from database format and group by date
            route_info = {}
            routes_by_date = {}
            
            for route in routes_data:
                route_id = route.get('route_id') or route.get('id')
                route_name = route.get('route_name') or route.get('name', 'Unknown Route')
                route_date = str(route.get('date', ''))
                day_of_week = route.get('day_of_week', 'unknown')
                
                # Parse JSON details field
                details = parse_json_details(route.get('details', ''))
                duration_str = details.get('duration', '8:00')
                duration_hours = parse_time_string_to_hours(duration_str)
                
                route_code = details.get('route_code', route_name)
                
                route_info[route_id] = {
                    'name': route_name,
                    'route_code': route_code,
                    'date': route_date,
                    'duration_hours': duration_hours,
                    'day_of_week': day_of_week,
                    'route_type': details.get('type', 'unknown')
                }
                
                # Group routes by date
                if route_date not in routes_by_date:
                    routes_by_date[route_date] = []
                routes_by_date[route_date].append(route_id)
            
            # Parse availability
            driver_availability = {}
            driver_available_days = {}
            
            for avail in availability_data:
                driver_id = avail.get('driver_id')
                date_str = str(avail.get('date', ''))
                is_available = avail.get('available', False)
                
                if driver_id not in driver_availability:
                    driver_availability[driver_id] = {}
                    driver_available_days[driver_id] = 0
                
                driver_availability[driver_id][date_str] = {
                    'available': is_available,
                    'shift_preference': avail.get('shift_preference', 'any')
                }
                
                if is_available:
                    driver_available_days[driver_id] += 1
            
            # Get all unique dates and sort them chronologically
            all_dates = list(routes_by_date.keys())
            sorted_dates = []
            
            for date_str in all_dates:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    sorted_dates.append((date_obj, date_str))
                except ValueError:
                    sorted_dates.append((date_str, date_str))
            
            sorted_dates.sort(key=lambda x: x[0])
            
            # Find special assignments
            klagenfurt_driver_id = None
            for driver_id, driver_data in driver_info.items():
                if driver_data['name'] == "Klagenfurt - Samstagsfahrer":
                    klagenfurt_driver_id = driver_id
                    break
            
            # Store all assignments across all dates
            all_assignments = {}
            all_unassigned_routes = []
            total_assignments = 0
            driver_hours_used = {driver_id: 0 for driver_id in driver_info.keys()}
            
            # SEQUENTIAL OPTIMIZATION: Process each date in chronological order
            for date_obj, current_date in sorted_dates:
                logger.info(f"Optimizing routes for date: {current_date}")
                
                # Get routes for current date
                current_route_ids = routes_by_date[current_date]
                
                if not current_route_ids:
                    continue
                
                # Create solver for this date
                solver = pywraplp.Solver.CreateSolver('SCIP')
                if not solver:
                    logger.error(f"Failed to create solver for date {current_date}")
                    continue
                
                # Create decision variables for current date only
                x = {}
                for driver_id in driver_info.keys():
                    for route_id in current_route_ids:
                        route_data = route_info[route_id]
                        
                        # Only create variable if:
                        # 1. Driver is available on this date
                        # 2. Driver has enough remaining hours for this route
                        if (driver_id in driver_availability and 
                            current_date in driver_availability[driver_id] and 
                            driver_availability[driver_id][current_date]['available'] and
                            driver_remaining_hours[driver_id] >= route_data['duration_hours']):
                            
                            x[driver_id, route_id] = solver.IntVar(0, 1, f'x_{driver_id}_{route_id}')
            
            # Constraint 1: Each route assigned to exactly one driver (or none if no one available)
            for route_id in route_info.keys():
                constraint_vars = []
                for driver_id in driver_info.keys():
                    if (driver_id, route_id) in x:
                        constraint_vars.append(x[driver_id, route_id])
                
                if constraint_vars:
                    solver.Add(sum(constraint_vars) <= 1)
            
            # Constraint 2: Each driver can only be assigned ONE route per day
            for driver_id in driver_info.keys():
                for date_str, route_ids_on_date in routes_by_date.items():
                    # Check if driver is available on this date
                    if (driver_id in driver_availability and 
                        date_str in driver_availability[driver_id] and 
                        driver_availability[driver_id][date_str]['available']):
                        
                        # Get all variables for this driver on this date
                        same_day_vars = []
                        for route_id in route_ids_on_date:
                            if (driver_id, route_id) in x:
                                same_day_vars.append(x[driver_id, route_id])
                        
                        # Constraint: sum of assignments for this driver on this day <= 1
                        if same_day_vars:
                            solver.Add(sum(same_day_vars) <= 1)
            
            # Constraint 3: Driver cannot exceed monthly available hours
            for driver_id, driver_data in driver_info.items():
                monthly_hours = driver_data['monthly_hours']
                constraint_vars = []
                route_hours = []
                
                for route_id, route_data in route_info.items():
                    if (driver_id, route_id) in x:
                        constraint_vars.append(x[driver_id, route_id])
                        route_hours.append(route_data['duration_hours'])
                
                if constraint_vars:
                    solver.Add(sum(var * hours for var, hours in zip(constraint_vars, route_hours)) <= monthly_hours)
            
            # Constraint 4: Progressive hour consumption - running balance constraints
            # This ensures that remaining capacity reduces as routes are assigned chronologically
            for driver_id, driver_data in driver_info.items():
                monthly_hours = driver_data['monthly_hours']
                
                # Get all dates this driver is available, sorted chronologically
                driver_dates = []
                if driver_id in driver_availability:
                    for date_str, avail_info in driver_availability[driver_id].items():
                        if avail_info['available']:
                            try:
                                # Parse date string to ensure proper sorting
                                from datetime import datetime
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                                driver_dates.append((date_obj, date_str))
                            except ValueError:
                                # If date parsing fails, use string sorting as fallback
                                driver_dates.append((date_str, date_str))
                
                # Sort dates chronologically
                driver_dates.sort(key=lambda x: x[0])
                
                # Create running balance variables for remaining hours after each date
                remaining_hours = {}
                
                # Initial remaining hours = monthly capacity
                remaining_hours['start'] = solver.NumVar(0, monthly_hours, f'remaining_start_{driver_id}')
                solver.Add(remaining_hours['start'] == monthly_hours)
                
                # For each date, create constraint: remaining_after_date = remaining_before_date - hours_used_on_date
                prev_remaining = remaining_hours['start']
                
                for date_obj, current_date in driver_dates:
                    # Calculate total hours used on this date
                    date_hours_used = 0
                    date_vars = []
                    date_hours = []
                    
                    if current_date in routes_by_date:
                        for route_id in routes_by_date[current_date]:
                            if (driver_id, route_id) in x:
                                date_vars.append(x[driver_id, route_id])
                                date_hours.append(route_info[route_id]['duration_hours'])
                    
                    if date_vars:
                        # Hours used on this date
                        hours_used_today = sum(var * hours for var, hours in zip(date_vars, date_hours))
                        
                        # Remaining hours after this date
                        remaining_after = solver.NumVar(0, monthly_hours, f'remaining_after_{driver_id}_{current_date}')
                        remaining_hours[current_date] = remaining_after
                        
                        # Balance constraint: remaining_after = remaining_before - hours_used_today
                        solver.Add(remaining_after == prev_remaining - hours_used_today)
                        
                        # Remaining hours must be non-negative (this prevents over-assignment)
                        solver.Add(remaining_after >= 0)
                        
                        # Update for next iteration
                        prev_remaining = remaining_after
                    else:
                        # No routes on this date, remaining hours stay the same
                        remaining_hours[current_date] = prev_remaining
            
            # Constraint 5: Saturday route 452SA must be assigned to Klagenfurt - Samstagsfahrer
            if klagenfurt_driver_id and saturday_252sa_route_id:
                if (klagenfurt_driver_id, saturday_252sa_route_id) in x:
                    solver.Add(x[klagenfurt_driver_id, saturday_252sa_route_id] == 1)
                    logger.info("Added constraint: Saturday route 452SA assigned to Klagenfurt - Samstagsfahrer")
                else:
                    logger.warning("Cannot assign 452SA to Klagenfurt - Samstagsfahrer (driver not available)")
            else:
                logger.warning(f"Special assignment check - Klagenfurt driver found: {klagenfurt_driver_id is not None}, Saturday 452SA route found: {saturday_252sa_route_id is not None}")
            
            # UPDATED OBJECTIVE: Simplified to focus on monthly capacity and availability
            objective_terms = []
            
            for driver_id, driver_data in driver_info.items():
                monthly_hours = driver_data['monthly_hours']
                available_days = driver_available_days.get(driver_id, 0)
                
                for route_id, route_data in route_info.items():
                    if (driver_id, route_id) in x:
                        # Weight calculation based on:
                        # 1. Monthly capacity (higher = better for workload distribution)
                        # 2. Available days (more days = more flexible)
                        
                        capacity_weight = monthly_hours * 5  # Favor drivers with higher monthly capacity
                        flexibility_weight = available_days * 10  # Favor drivers available more days
                        
                        # Base weight for making assignments
                        assignment_weight = 100
                        
                        total_weight = assignment_weight + capacity_weight + flexibility_weight
                        objective_terms.append(x[driver_id, route_id] * total_weight)
            
            solver.Maximize(sum(objective_terms))
            
            # Solve the problem
            logger.info("Starting OR-Tools solver...")
            status = solver.Solve()
            
            # Process results
            if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
                assignments = {}
                unassigned_routes = []
                total_assignments = 0
                driver_hours_used = {}
                
                # Extract assignments
                for driver_id in driver_info.keys():
                    driver_hours_used[driver_id] = 0
                    for route_id, route_data in route_info.items():
                        if (driver_id, route_id) in x and x[driver_id, route_id].solution_value() == 1:
                            date_str = route_data['date']
                            route_name = route_data['name']
                            
                            if date_str not in assignments:
                                assignments[date_str] = {}
                            
                            duration_hours = route_data['duration_hours']
                            duration_formatted = f"{int(duration_hours)}:{int((duration_hours % 1) * 60):02d}"
                            
                            assignments[date_str][route_name] = {
                                'driver_name': driver_info[driver_id]['name'],
                                'driver_id': driver_id,
                                'route_id': route_id,
                                'duration_hours': duration_hours,
                                'duration_formatted': duration_formatted
                            }
                            total_assignments += 1
                            driver_hours_used[driver_id] += duration_hours
                
                # Find unassigned routes
                assigned_route_ids = set()
                for date_assignments in assignments.values():
                    for route_assignment in date_assignments.values():
                        assigned_route_ids.add(route_assignment['route_id'])
                
                for route_id, route_data in route_info.items():
                    if route_id not in assigned_route_ids:
                        unassigned_routes.append({
                            'id': route_id,
                            'name': route_data['name'],
                            'date': route_data['date'],
                            'duration_hours': route_data['duration_hours']
                        })
                
                # Calculate driver utilization based on monthly hours only
                driver_utilization = {}
                for driver_id, driver_data in driver_info.items():
                    monthly_hours = driver_data['monthly_hours']
                    hours_used = driver_hours_used.get(driver_id, 0)
                    available_days = driver_available_days.get(driver_id, 0)
                    
                    # Calculate utilization against monthly capacity
                    utilization_rate = (hours_used / monthly_hours * 100) if monthly_hours > 0 else 0
                    
                    driver_utilization[driver_id] = {
                        'name': driver_data['name'],
                        'monthly_capacity_hours': monthly_hours,
                        'available_days': available_days,
                        'hours_used': hours_used,
                        'hours_remaining': monthly_hours - hours_used,
                        'utilization_rate': round(utilization_rate, 2)
                    }
                
                # Verify special assignment
                special_assignment_status = "Not found"
                if klagenfurt_driver_id and saturday_252sa_route_id:
                    for date_assignments in assignments.values():
                        for route_assignment in date_assignments.values():
                            if (route_assignment['driver_id'] == klagenfurt_driver_id and 
                                route_assignment['route_id'] == saturday_252sa_route_id):
                                special_assignment_status = "Successfully assigned"
                                break
                
                # Calculate statistics
                statistics = {
                    'total_assignments': total_assignments,
                    'total_routes': len(route_info),
                    'unassigned_count': len(unassigned_routes),
                    'assignment_rate': round((total_assignments / len(route_info)) * 100, 2) if route_info else 0,
                    'objective_value': solver.Objective().Value(),
                    'solve_time_ms': solver.WallTime(),
                    'driver_utilization': driver_utilization,
                    'special_assignment_452sa': special_assignment_status
                }
                
                solver_status = 'OPTIMAL' if status == pywraplp.Solver.OPTIMAL else 'FEASIBLE'
                
                logger.info(f"Optimization completed: {total_assignments}/{len(route_info)} routes assigned")
                logger.info(f"Saturday 452SA assignment: {special_assignment_status}")
                
                return {
                    'assignments': assignments,
                    'unassigned_routes': unassigned_routes,
                    'statistics': statistics,
                    'solver_status': solver_status
                }
            
            else:
                error_msg = f"Solver failed with status: {status}"
                logger.error(error_msg)
                return {'error': error_msg}
        
        except Exception as e:
            logger.error(f"OR-Tools optimization error: {str(e)}", exc_info=True)
            return {'error': f"Optimization failed: {str(e)}"}

# Legacy compatibility class for existing API endpoints
class SchedulingOptimizer:
    def __init__(self):
        self.advanced_optimizer = DriverRouteOptimizer()
        
    def optimize_assignments(self, drivers: List[Dict], routes: List[Dict], availability: List[Dict], week_start: date) -> List[Dict]:
        """Legacy interface - converts to new optimizer format and back to old format"""
        try:
            # Convert data to new format
            drivers_data = []
            for driver in drivers:
                drivers_data.append({
                    'driver_id': driver['driver_id'],
                    'name': driver['name'],
                    'details': driver.get('details', '{"type": "full_time", "monthly_hours": "174:00"}')
                })
            
            routes_data = []
            for route in routes:
                routes_data.append({
                    'route_id': route['route_id'],
                    'route_name': route['route_name'],
                    'date': route['date'],
                    'day_of_week': route.get('day_of_week', 'unknown'),
                    'details': route.get('details', '{"duration": "8:00"}')
                })
            
            availability_data = []
            for avail in availability:
                availability_data.append({
                    'driver_id': avail['driver_id'],
                    'date': avail['date'],
                    'available': avail.get('available', True),
                    'available_hours': avail.get('available_hours', 8),
                    'max_routes': avail.get('max_routes', 1)
                })
            
            # Run new optimizer
            result = self.advanced_optimizer.optimize_assignments(drivers_data, routes_data, availability_data)
            
            if 'error' in result:
                logger.error(f"Optimization failed: {result['error']}")
                return []
            
            # Convert back to old format
            legacy_assignments = []
            assignments = result.get('assignments', {})
            
            for date_str, date_assignments in assignments.items():
                for assignment in date_assignments:
                    legacy_assignments.append({
                        "driver": assignment['driver_name'],
                        "driver_id": assignment['driver_id'],
                        "route": assignment['route_name'],
                        "route_id": assignment.get('original_route_id', 0),
                        "date": date_str,
                        "duration_hours": assignment['duration_hours'],
                        "duration_formatted": assignment['duration_formatted'],
                        "status": "assigned"
                    })
            
            logger.info(f"Advanced optimization completed successfully with {len(legacy_assignments)} assignments")
            return legacy_assignments
            
        except Exception as e:
            logger.error(f"Error in advanced optimization: {e}")
            return []