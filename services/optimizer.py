"""
OR-Tools Driver Route Assignment Optimization - Sequential Algorithm
Handles exact database format and optimizes driver-route assignments day by day
- Sequential optimization: solves each day in chronological order
- Updates remaining hours between days for accurate capacity tracking
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
        
        for route_date in sorted(routes_by_date.keys()):
            date_str = route_date.strftime('%Y-%m-%d') if hasattr(route_date, 'strftime') else str(route_date)
            day_name = route_date.strftime('%A').lower() if hasattr(route_date, 'strftime') else 'unknown'
            
            logger.info(f"Processing date: {date_str} ({day_name})")
            
            date_routes = routes_by_date[route_date]
            fixed_assignments = []
            remaining_routes = []
            
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
                    total_assigned += 1
                    assignment['assignment_type'] = 'optimized'
            else:
                optimized_assignments = []
            
            # Combine fixed and optimized assignments for this date
            all_date_assignments = fixed_assignments + optimized_assignments
            final_assignments[date_str] = {route_assignment['route_name']: {
                'driver_name': route_assignment['driver_name'],
                'driver_id': route_assignment['driver_id'],
                'duration_hours': route_assignment['duration_hours'],
                'status': 'assigned',
                'assignment_type': route_assignment['assignment_type']
            } for route_assignment in all_date_assignments}
        
        logger.info(f"Enhanced optimization completed: {total_assigned} total routes assigned ({len(fixed_routes or [])} fixed rules applied)")
        
        return {
            'status': 'success',
            'assignments': final_assignments,
            'total_routes': sum(len(routes) for routes in routes_by_date.values()),
            'total_assigned': total_assigned,
            'fixed_rules_applied': len(fixed_routes or []),
            'solver_status': 'OPTIMAL_WITH_FIXED_ROUTES'
        }
        
    except Exception as e:
        logger.error(f"Enhanced optimization failed: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'assignments': {},
            'total_routes': 0,
            'total_assigned': 0
        }

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

def run_ortools_optimization(drivers: List[Dict], routes: List[Dict], availability: List[Dict]) -> Dict:
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
        
        for driver in drivers:
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
        
        for route in routes:
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
        
        logger.info(f"Loading availability data for {len(availability)} availability records")
        
        for avail in availability:
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
            
            # Debug log unavailable drivers
            if not is_available:
                driver_name = driver_info.get(driver_id, {}).get('name', f'Driver_{driver_id}')
                logger.info(f"Loaded unavailable: {driver_name} on {date_str}")
            
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
        
        # Pre-populate assignments with "F" for unavailable drivers on each date
        total_f_entries = 0
        for date_obj, date_str in sorted_dates:
            all_assignments[date_str] = {}
            
            # For each driver, check if they're unavailable on this date
            for driver_id, driver_data in driver_info.items():
                is_available = True  # Default to available if no data
                
                if driver_id in driver_availability:
                    if date_str in driver_availability[driver_id]:
                        is_available = driver_availability[driver_id][date_str]['available']
                        if not is_available:
                            logger.info(f"Found unavailable: {driver_data['name']} on {date_str}")
                    else:
                        logger.debug(f"No availability data for {driver_data['name']} on {date_str}")
                else:
                    logger.debug(f"No availability data for driver {driver_data['name']} (ID: {driver_id})")
                
                # If driver is unavailable, assign "F" with 0 hours
                if not is_available:
                    f_key = f"F_{driver_data['name']}_{date_str}"
                    all_assignments[date_str][f_key] = {
                        'driver_name': driver_data['name'],
                        'driver_id': driver_id,
                        'route_id': None,
                        'duration_hours': 0.0,
                        'duration_formatted': "00:00",
                        'status': 'unavailable'
                    }
                    total_f_entries += 1
                    logger.info(f"Created F entry: {driver_data['name']} unavailable on {date_str}")
        
        logger.info(f"Created {total_f_entries} F entries for unavailable drivers")
        
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
            
            # Constraint 1: Each route assigned to at most one driver
            for route_id in current_route_ids:
                constraint_vars = []
                for driver_id in driver_info.keys():
                    if (driver_id, route_id) in x:
                        constraint_vars.append(x[driver_id, route_id])
                
                if constraint_vars:
                    solver.Add(sum(constraint_vars) <= 1)
            
            # Constraint 2: Each driver can only be assigned one route per day
            for driver_id in driver_info.keys():
                same_day_vars = []
                for route_id in current_route_ids:
                    if (driver_id, route_id) in x:
                        same_day_vars.append(x[driver_id, route_id])
                
                if same_day_vars:
                    solver.Add(sum(same_day_vars) <= 1)
            
            # Constraint 3: Driver remaining hours constraint (UPDATED DYNAMICALLY)
            for driver_id in driver_info.keys():
                remaining_hours = driver_remaining_hours[driver_id]
                constraint_vars = []
                route_hours = []
                
                for route_id in current_route_ids:
                    if (driver_id, route_id) in x:
                        constraint_vars.append(x[driver_id, route_id])
                        route_hours.append(route_info[route_id]['duration_hours'])
                
                if constraint_vars:
                    solver.Add(sum(var * hours for var, hours in zip(constraint_vars, route_hours)) <= remaining_hours)
            
            # Constraint 4: Special assignment for Saturday 452SA
            saturday_452sa_route_id = None
            for route_id in current_route_ids:
                route_data = route_info[route_id]
                if route_data['name'] == '452SA' and route_data['day_of_week'] == 'saturday':
                    saturday_452sa_route_id = route_id
                    break
            
            if klagenfurt_driver_id and saturday_452sa_route_id:
                if (klagenfurt_driver_id, saturday_452sa_route_id) in x:
                    solver.Add(x[klagenfurt_driver_id, saturday_452sa_route_id] == 1)
                    logger.info(f"Added constraint: Saturday route 452SA assigned to Klagenfurt - Samstagsfahrer on {current_date}")
            
            # Objective: Prioritize drivers with more remaining capacity and availability
            objective_terms = []
            for driver_id in driver_info.keys():
                remaining_hours = driver_remaining_hours[driver_id]
                available_days = driver_available_days.get(driver_id, 0)
                
                for route_id in current_route_ids:
                    if (driver_id, route_id) in x:
                        # Weight based on remaining capacity and flexibility
                        capacity_weight = remaining_hours * 5
                        flexibility_weight = available_days * 10
                        assignment_weight = 100
                        
                        total_weight = assignment_weight + capacity_weight + flexibility_weight
                        objective_terms.append(x[driver_id, route_id] * total_weight)
            
            if objective_terms:
                solver.Maximize(sum(objective_terms))
            
            # Solve for current date
            status = solver.Solve()
            
            # Process results for current date
            if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
                # Extract assignments for current date (add to existing F assignments)
                for driver_id in driver_info.keys():
                    for route_id in current_route_ids:
                        if (driver_id, route_id) in x and x[driver_id, route_id].solution_value() == 1:
                            route_data = route_info[route_id]
                            route_name = route_data['name']
                            duration_hours = route_data['duration_hours']
                            duration_formatted = f"{int(duration_hours)}:{int((duration_hours % 1) * 60):02d}"
                            
                            # Add actual route assignment (overwrites any F assignment for this driver)
                            all_assignments[current_date][route_name] = {
                                'driver_name': driver_info[driver_id]['name'],
                                'driver_id': driver_id,
                                'route_id': route_id,
                                'duration_hours': duration_hours,
                                'duration_formatted': duration_formatted,
                                'status': 'assigned'
                            }
                            
                            # CRITICAL: Update remaining hours for this driver
                            driver_remaining_hours[driver_id] -= duration_hours
                            driver_hours_used[driver_id] += duration_hours
                            total_assignments += 1
                            
                            logger.info(f"Assigned {route_name} to {driver_info[driver_id]['name']} ({duration_hours}h). Remaining: {driver_remaining_hours[driver_id]:.1f}h")
                
                # Find unassigned routes for current date
                assigned_route_names = {route_name for route_name, details in all_assignments[current_date].items() 
                                      if not route_name.startswith('F_') and details.get('status') == 'assigned'}
                
                for route_id in current_route_ids:
                    route_data = route_info[route_id]
                    route_name = route_data['name']
                    
                    if route_name not in assigned_route_names:
                        all_unassigned_routes.append({
                            'id': route_id,
                            'name': route_name,
                            'date': route_data['date'],
                            'duration_hours': route_data['duration_hours']
                        })
                        logger.warning(f"Route {route_name} on {current_date} could not be assigned")
            
            else:
                logger.error(f"Solver failed for date {current_date} with status: {status}")
                # Add all routes for this date to unassigned (F assignments remain)
                for route_id in current_route_ids:
                    route_data = route_info[route_id]
                    all_unassigned_routes.append({
                        'id': route_id,
                        'name': route_data['name'],
                        'date': route_data['date'],
                        'duration_hours': route_data['duration_hours']
                    })
        
        # Calculate final driver utilization
        driver_utilization = {}
        for driver_id, driver_data in driver_info.items():
            monthly_hours = driver_data['monthly_hours']
            hours_used = driver_hours_used[driver_id]
            available_days = driver_available_days.get(driver_id, 0)
            
            utilization_rate = (hours_used / monthly_hours * 100) if monthly_hours > 0 else 0
            
            driver_utilization[driver_id] = {
                'name': driver_data['name'],
                'monthly_capacity_hours': monthly_hours,
                'available_days': available_days,
                'hours_used': hours_used,
                'hours_remaining': driver_remaining_hours[driver_id],
                'utilization_rate': round(utilization_rate, 2)
            }
        
        # Verify special assignment
        special_assignment_status = "Not found"
        if klagenfurt_driver_id:
            for date_assignments in all_assignments.values():
                for route_name, assignment_details in date_assignments.items():
                    if (assignment_details['driver_id'] == klagenfurt_driver_id and 
                        route_name == '452SA'):
                        special_assignment_status = "Successfully assigned"
                        break
        
        # Calculate statistics
        statistics = {
            'total_assignments': total_assignments,
            'total_routes': len(route_info),
            'unassigned_count': len(all_unassigned_routes),
            'assignment_rate': round((total_assignments / len(route_info)) * 100, 2) if route_info else 0,
            'objective_value': 0,  # Not applicable for sequential solving
            'solve_time_ms': 0,    # Not applicable for sequential solving
            'driver_utilization': driver_utilization,
            'special_assignment_452sa': special_assignment_status
        }
        
        logger.info(f"Sequential optimization completed: {total_assignments}/{len(route_info)} routes assigned")
        logger.info(f"Saturday 452SA assignment: {special_assignment_status}")
        
        # Debug: Log F entries being returned
        f_entries_count = 0
        for date_str, date_assignments in all_assignments.items():
            for route_name, assignment_details in date_assignments.items():
                if route_name.startswith('F_'):
                    f_entries_count += 1
        
        if f_entries_count > 0:
            logger.info(f"Optimizer returning {f_entries_count} F entries for unavailable drivers")
        
        return {
            'assignments': all_assignments,
            'unassigned_routes': all_unassigned_routes,
            'statistics': statistics,
            'solver_status': 'SEQUENTIAL_OPTIMAL'
        }
    
    except Exception as e:
        logger.error(f"OR-Tools sequential optimization error: {str(e)}", exc_info=True)
        return {'error': f"Sequential optimization failed: {str(e)}"}

class DriverRouteOptimizer:
    def __init__(self):
        self.solver = None
        
    def optimize_assignments(self, drivers_data: List[Dict], routes_data: List[Dict], 
                           availability_data: List[Dict]) -> Dict:
        """
        Run sequential OR-Tools optimization for driver-route assignment
        """
        return run_ortools_optimization(drivers_data, routes_data, availability_data)

# Legacy compatibility class for existing API endpoints
class SchedulingOptimizer:
    def __init__(self):
        self.advanced_optimizer = DriverRouteOptimizer()
        
    def optimize_schedule(self, drivers_data: List[Dict], routes_data: List[Dict], 
                         availability_data: List[Dict]) -> Dict:
        """Legacy method for backward compatibility"""
        return self.advanced_optimizer.optimize_assignments(drivers_data, routes_data, availability_data)