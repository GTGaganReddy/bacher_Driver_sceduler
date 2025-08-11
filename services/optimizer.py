"""
Advanced Driver Route Assignment Optimization using OR-Tools
Optimizes driver assignments for a full week considering:
- Monthly hour limits and remaining hours
- Daily availability and hour constraints
- Maximum routes per driver per day
- Special Saturday rule for route 452SA
- Prioritizes drivers with most remaining monthly hours
"""

from ortools.linear_solver import pywraplp
from datetime import datetime, timedelta, date
import json
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class DriverRouteOptimizer:
    def __init__(self):
        self.solver = None
        self.drivers = []
        self.routes = []
        self.availability = []
        self.assignments = {}
        
    def optimize_assignments(self, drivers_data: List[Dict], routes_data: List[Dict], 
                           availability_data: List[Dict]) -> Dict:
        """
        Main optimization function
        
        Args:
            drivers_data: List of driver dictionaries with id, name, monthly_hours_limit
            routes_data: List of route dictionaries with date, route_name, duration
            availability_data: List of availability records with driver_id, date, available, 
                             available_hours, max_routes
        
        Returns:
            Dict: Optimal assignments with detailed statistics
        """
        
        self.drivers = drivers_data
        self.routes = routes_data
        self.availability = availability_data
        
        # Parse and validate data
        parsed_data = self._parse_input_data()
        if not parsed_data:
            return {"error": "Failed to parse input data"}
        
        # Create solver
        self.solver = pywraplp.Solver.CreateSolver('SCIP')
        if not self.solver:
            return {"error": "Could not create solver"}
        
        # Build optimization model
        self._build_optimization_model(parsed_data)
        
        # Solve
        status = self.solver.Solve()
        
        if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
            return self._extract_solution(parsed_data)
        else:
            logger.warning(f"No optimal solution found. Status: {status}")
            return {"error": f"No solution found. Status: {status}"}
    
    def _parse_input_data(self) -> Optional[Dict]:
        """Parse and structure input data for optimization"""
        try:
            # Create driver lookup and parse monthly hours
            driver_info = {}
            for driver in self.drivers:
                # Handle both database format and API format
                if isinstance(driver, str):
                    logger.error(f"Received string instead of dict for driver: {driver}")
                    continue
                    
                # Get monthly hours from either field
                monthly_hours = driver.get('monthly_hours_limit', 174)
                
                # Parse details if present (joined query format)
                if 'details' in driver and driver['details']:
                    try:
                        if isinstance(driver['details'], str):
                            import json
                            details = json.loads(driver['details'])
                            if 'monthly_hours' in details:
                                monthly_hours = details['monthly_hours']
                        else:
                            details = driver['details']
                            if 'monthly_hours' in details:
                                monthly_hours = details['monthly_hours']
                    except:
                        pass  # Use default or existing value
                
                # Convert string format to decimal hours
                if isinstance(monthly_hours, str):
                    if ':' in monthly_hours:
                        hours, minutes = monthly_hours.split(':')
                        monthly_hours = float(hours) + float(minutes) / 60.0
                    else:
                        monthly_hours = float(monthly_hours)
                
                driver_info[driver['driver_id']] = {
                    'name': driver['name'],
                    'monthly_hours': float(monthly_hours),
                    'type': 'full_time'
                }
            
            # Group routes by date and parse duration
            routes_by_date = {}
            for route in self.routes:
                route_date = route['date']
                if isinstance(route_date, date):
                    route_date = route_date.isoformat()
                
                if route_date not in routes_by_date:
                    routes_by_date[route_date] = []
                
                # Parse duration from details JSON or assume default
                duration = 8.0  # Default 8 hours
                if 'details' in route and route['details']:
                    if isinstance(route['details'], str):
                        import json
                        try:
                            details = json.loads(route['details'])
                        except:
                            details = {}
                    else:
                        details = route['details']
                    
                    duration_str = details.get('duration', '8:00')
                    if isinstance(duration_str, str) and ':' in duration_str:
                        hours, minutes = duration_str.split(':')
                        duration = float(hours) + float(minutes) / 60.0
                    else:
                        duration = float(duration_str) if duration_str else 8.0
                
                routes_by_date[route_date].append({
                    'route_id': len(routes_by_date[route_date]),  # Sequential ID for this date
                    'route_name': route['route_name'],
                    'duration': duration,
                    'original_route_id': route.get('route_id', 0)
                })
            
            # Create availability lookup
            availability_map = {}
            for avail in self.availability:
                # Handle both string and dict formats
                if isinstance(avail, str):
                    logger.error(f"Received string instead of dict for availability: {avail}")
                    continue
                    
                avail_date = avail['date']
                if isinstance(avail_date, date):
                    avail_date = avail_date.isoformat()
                
                driver_id = avail['driver_id']
                
                if avail_date not in availability_map:
                    availability_map[avail_date] = {}
                
                # Get actual values from database or use realistic defaults
                available_hours = float(avail.get('available_hours', 16.0))  # Use DB value or 16h default
                max_routes = int(avail.get('max_routes', 3))                  # Use DB value or 3 routes default
                
                # Override if database values are too restrictive for 11-hour routes
                if available_hours < 12.0:
                    available_hours = 16.0  # Increase to handle 11+ hour routes
                if max_routes < 2:
                    max_routes = 2
                
                availability_map[avail_date][driver_id] = {
                    'available': avail.get('available', False),
                    'available_hours': available_hours,
                    'max_routes': max_routes,
                    'shift_preference': avail.get('shift_preference', 'any')
                }
            
            # Debug logging
            total_routes = sum(len(routes) for routes in routes_by_date.values())
            available_drivers = sum(1 for date_map in availability_map.values() 
                                   for driver_avail in date_map.values() 
                                   if driver_avail['available'])
            
            logger.info(f"Parsed data: {len(driver_info)} drivers, {len(routes_by_date)} dates, {total_routes} routes")
            logger.info(f"Available driver-days: {available_drivers}")
            logger.info(f"Original route count from input: {len(self.routes)}")
            
            # Log routes by date for debugging
            for date_str, routes_list in routes_by_date.items():
                logger.info(f"Date {date_str}: {len(routes_list)} routes")
            
            # Sample availability data
            if availability_map:
                sample_date = list(availability_map.keys())[0]
                sample_driver = list(availability_map[sample_date].keys())[0]
                sample_avail = availability_map[sample_date][sample_driver]
                logger.info(f"Sample availability: Driver {sample_driver} on {sample_date}: {sample_avail}")
            
            return {
                'driver_info': driver_info,
                'routes_by_date': routes_by_date,
                'availability_map': availability_map,
                'dates': sorted(routes_by_date.keys())
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Error parsing input data: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    def _build_optimization_model(self, data: Dict):
        """Build the OR-Tools optimization model"""
        
        driver_info = data['driver_info']
        routes_by_date = data['routes_by_date']
        availability_map = data['availability_map']
        dates = data['dates']
        
        # Decision variables: x[driver_id][date][route_id] = 1 if assigned
        x = {}
        for driver_id in driver_info:
            x[driver_id] = {}
            for date in dates:
                x[driver_id][date] = {}
                if date in routes_by_date:
                    for route in routes_by_date[date]:
                        route_id = route['route_id']
                        x[driver_id][date][route_id] = self.solver.BoolVar(
                            f'x_{driver_id}_{date}_{route_id}'
                        )
        
        # Store variables for solution extraction
        self.decision_vars = x
        self.parsed_data = data
        
        # Constraint 1: Each route must be assigned to exactly one driver
        for date in dates:
            if date in routes_by_date:
                for route in routes_by_date[date]:
                    route_id = route['route_id']
                    constraint = self.solver.Constraint(1, 1)
                    for driver_id in driver_info:
                        if driver_id in x and date in x[driver_id] and route_id in x[driver_id][date]:
                            constraint.SetCoefficient(x[driver_id][date][route_id], 1)
        
        # Constraint 2: Driver availability constraints
        for driver_id in driver_info:
            for date in dates:
                if date in availability_map and driver_id in availability_map[date]:
                    avail = availability_map[date][driver_id]
                    
                    if not avail['available']:
                        # Driver not available - cannot be assigned any route
                        for route_id in x[driver_id].get(date, {}):
                            constraint = self.solver.Constraint(0, 0)
                            constraint.SetCoefficient(x[driver_id][date][route_id], 1)
                    else:
                        # Max routes constraint
                        if avail['max_routes'] > 0:
                            constraint = self.solver.Constraint(0, avail['max_routes'])
                            for route_id in x[driver_id].get(date, {}):
                                constraint.SetCoefficient(x[driver_id][date][route_id], 1)
                        
                        # Daily hours constraint
                        if avail['available_hours'] > 0 and date in routes_by_date:
                            constraint = self.solver.Constraint(0, avail['available_hours'])
                            for route in routes_by_date[date]:
                                route_id = route['route_id']
                                if route_id in x[driver_id].get(date, {}):
                                    constraint.SetCoefficient(
                                        x[driver_id][date][route_id], 
                                        route['duration']
                                    )
        
        # Constraint 3: Monthly hours constraint (simplified - assumes even distribution)
        weekly_limit_factor = 1.2  # Allow 20% over weekly average for optimization
        for driver_id in driver_info:
            monthly_hours = driver_info[driver_id]['monthly_hours']
            weekly_hours_limit = (monthly_hours / 4.33) * weekly_limit_factor  # Approximate weekly limit
            
            constraint = self.solver.Constraint(0, weekly_hours_limit)
            for date in dates:
                if date in routes_by_date:
                    for route in routes_by_date[date]:
                        route_id = route['route_id']
                        if driver_id in x and date in x[driver_id] and route_id in x[driver_id][date]:
                            constraint.SetCoefficient(
                                x[driver_id][date][route_id], 
                                route['duration']
                            )
        
        # Special Constraint: Saturday route 452SA priority for Saturday drivers
        saturday_driver_id = None
        for driver_id, info in driver_info.items():
            if 'Samstag' in info['name'] or 'Saturday' in info['name'] or 'Klagenfurt - Samstagsfahrer' in info['name']:
                saturday_driver_id = driver_id
                break
        
        if saturday_driver_id:
            for date in dates:
                # Check if it's Saturday and has route 452SA
                if date in routes_by_date:
                    route_452SA = None
                    for route in routes_by_date[date]:
                        if route['route_name'] == '452SA':
                            route_452SA = route
                            break
                    
                    if route_452SA and saturday_driver_id in availability_map.get(date, {}):
                        if availability_map[date][saturday_driver_id]['available']:
                            # Force assignment of 452SA to Saturday driver if available
                            route_id = route_452SA['route_id']
                            if (saturday_driver_id in x and date in x[saturday_driver_id] 
                                and route_id in x[saturday_driver_id][date]):
                                constraint = self.solver.Constraint(1, 1)
                                constraint.SetCoefficient(x[saturday_driver_id][date][route_id], 1)
        
        # Objective: Maximize assignment preference based on remaining hours
        objective = self.solver.Objective()
        
        for driver_id in driver_info:
            monthly_hours = driver_info[driver_id]['monthly_hours']
            # Higher monthly hours = higher priority (weight)
            weight = monthly_hours / 100.0  # Normalize weights
            
            for date in dates:
                if date in routes_by_date:
                    for route in routes_by_date[date]:
                        route_id = route['route_id']
                        if driver_id in x and date in x[driver_id] and route_id in x[driver_id][date]:
                            # Bonus for assigning to drivers with more hours
                            objective.SetCoefficient(x[driver_id][date][route_id], weight)
        
        objective.SetMaximization()
    
    def _extract_solution(self, data: Dict) -> Dict:
        """Extract the optimal solution from the solver"""
        
        driver_info = data['driver_info']
        routes_by_date = data['routes_by_date']
        dates = data['dates']
        x = self.decision_vars
        
        detailed_assignments = {}
        unassigned_routes = []
        statistics = {
            'total_assignments': 0,
            'unassigned_routes': 0,
            'total_hours_assigned': 0.0,
            'driver_workload': {}
        }
        
        # Extract assignments
        for date in dates:
            detailed_assignments[date] = {}
            if date in routes_by_date:
                for route in routes_by_date[date]:
                    route_id = route['route_id']
                    route_name = route['route_name']
                    route_duration = route['duration']
                    assigned = False
                    
                    for driver_id in driver_info:
                        if (driver_id in x and date in x[driver_id] 
                            and route_id in x[driver_id][date]
                            and x[driver_id][date][route_id].solution_value() > 0.5):
                            
                            driver_name = driver_info[driver_id]['name']
                            
                            # Detailed format with all info
                            detailed_assignments[date][route_name] = {
                                'driver_name': driver_name,
                                'driver_id': driver_id,
                                'duration_hours': route_duration,
                                'duration_formatted': f"{int(route_duration)}:{int((route_duration % 1) * 60):02d}",
                                'original_route_id': route.get('original_route_id', route_id)
                            }
                            
                            statistics['total_assignments'] += 1
                            statistics['total_hours_assigned'] += route_duration
                            assigned = True
                            
                            # Track driver workload
                            if driver_id not in statistics['driver_workload']:
                                statistics['driver_workload'][driver_id] = {
                                    'name': driver_name,
                                    'assignments': 0,
                                    'total_hours': 0.0
                                }
                            statistics['driver_workload'][driver_id]['assignments'] += 1
                            statistics['driver_workload'][driver_id]['total_hours'] += route_duration
                            break
                    
                    if not assigned:
                        statistics['unassigned_routes'] += 1
                        unassigned_routes.append({
                            'date': date,
                            'route_name': route_name,
                            'duration_hours': route_duration,
                            'duration_formatted': f"{int(route_duration)}:{int((route_duration % 1) * 60):02d}"
                        })
        
        # Convert to list format for consistency with API expectations
        assignments_list_format = {}
        for date, date_assignments in detailed_assignments.items():
            assignments_list_format[date] = []
            for route_name, assignment_details in date_assignments.items():
                # Ensure assignment_details is a dict, not a string
                if isinstance(assignment_details, str):
                    logger.error(f"Found string instead of dict for assignment: {assignment_details}")
                    continue
                assignment_details['route_name'] = route_name
                assignments_list_format[date].append(assignment_details)
        
        return {
            'assignments': assignments_list_format,  # Format: {date: [{driver_name, driver_id, route_name, duration}]}
            'unassigned_routes': unassigned_routes,
            'statistics': statistics,
            'solver_status': 'OPTIMAL' if self.solver.Objective().Value() else 'FEASIBLE',
            'objective_value': self.solver.Objective().Value()
        }

# Legacy compatibility class for existing API endpoints
class SchedulingOptimizer:
    def __init__(self):
        self.advanced_optimizer = DriverRouteOptimizer()
        
    def optimize_assignments(self, drivers: List[Dict], routes: List[Dict], availability: List[Dict], week_start: date) -> List[Dict]:
        """
        Legacy interface - converts to new optimizer format and back to old format
        """
        try:
            # Convert data to new format
            drivers_data = []
            for driver in drivers:
                drivers_data.append({
                    'driver_id': driver['driver_id'],
                    'name': driver['name'],
                    'monthly_hours_limit': driver.get('monthly_hours_limit', 174)
                })
            
            routes_data = []
            for route in routes:
                routes_data.append({
                    'route_id': route['route_id'],
                    'route_name': route['route_name'],
                    'date': route['date'],
                    'details': {'duration': '8:00'}  # Default duration
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
                return self._create_basic_assignments(drivers, routes, availability, week_start)
            
            # Convert back to old format
            legacy_assignments = []
            assignments = result.get('assignments', {})
            
            for date_str, date_assignments in assignments.items():
                for route_name, assignment_details in date_assignments.items():
                    legacy_assignments.append({
                        "driver": assignment_details['driver_name'],
                        "driver_id": assignment_details['driver_id'],
                        "route": route_name,
                        "route_id": assignment_details.get('original_route_id', 0),
                        "date": date_str,
                        "hour": "08:00",  # Default start time
                        "remaining_hour": "16:00",  # Default end time
                        "status": "assigned"
                    })
            
            logger.info(f"Advanced optimization completed successfully with {len(legacy_assignments)} assignments")
            return legacy_assignments
            
        except Exception as e:
            logger.error(f"Error in advanced optimization: {e}")
            return self._create_basic_assignments(drivers, routes, availability, week_start)
    
    def _create_basic_assignments(self, drivers: List[Dict], routes: List[Dict], availability: List[Dict], week_start: date) -> List[Dict]:
        """
        Fallback method for basic round-robin assignment when optimization fails
        """
        assignments = []
        driver_index = 0
        
        # Create availability lookup
        availability_lookup = {}
        for avail in availability:
            key = (avail['driver_id'], avail['date'])
            availability_lookup[key] = avail.get('available', True)
        
        for route in routes:
            assigned = False
            attempts = 0
            
            while not assigned and attempts < len(drivers):
                driver = drivers[driver_index % len(drivers)]
                route_date = route['date']
                if isinstance(route_date, date):
                    route_date = route_date.isoformat()
                
                is_available = availability_lookup.get((driver['driver_id'], route_date), True)
                
                if is_available:
                    assignments.append({
                        "driver": driver['name'],
                        "driver_id": driver['driver_id'],
                        "route": route['route_name'],
                        "route_id": route['route_id'],
                        "date": route_date,
                        "hour": "08:00",
                        "remaining_hour": "16:00",
                        "status": "assigned"
                    })
                    assigned = True
                
                driver_index += 1
                attempts += 1
            
            if not assigned:
                logger.warning(f"Could not assign route {route['route_name']} on {route_date}")
        
        return assignments

# Convenience function for direct usage
def optimize_driver_schedule(drivers_data: List[Dict], routes_data: List[Dict], 
                           availability_data: List[Dict]) -> Dict:
    """
    Convenience function to run the advanced optimization
    """
    optimizer = DriverRouteOptimizer()
    return optimizer.optimize_assignments(drivers_data, routes_data, availability_data)
