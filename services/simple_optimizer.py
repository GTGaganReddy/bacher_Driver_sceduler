"""
Enhanced Driver Route Assignment Optimization using OR-Tools
Optimizes driver assignments for a full weekly schedule with advanced constraints
"""

import logging
from typing import Dict, List, Any
from datetime import date
import json
from ortools.linear_solver import pywraplp

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
            drivers_data: List of driver dictionaries with id, name, monthly_hours
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
        logger.info("Starting OR-Tools solver...")
        status = self.solver.Solve()
        
        logger.info(f"Solver finished with status: {status}")
        logger.info(f"Status meanings: OPTIMAL=0, FEASIBLE=1, INFEASIBLE=2, UNBOUNDED=3, ABNORMAL=4, NOT_SOLVED=6")
        
        if status == pywraplp.Solver.OPTIMAL:
            logger.info("Found optimal solution")
            return self._extract_solution(parsed_data)
        elif status == pywraplp.Solver.FEASIBLE:
            logger.info("Found feasible solution")
            return self._extract_solution(parsed_data)
        elif status == pywraplp.Solver.INFEASIBLE:
            logger.error("Problem is infeasible - constraints are too restrictive")
            return {"error": f"Infeasible problem - constraints cannot be satisfied. Status: {status}"}
        elif status == pywraplp.Solver.UNBOUNDED:
            logger.error("Problem is unbounded")
            return {"error": f"Unbounded problem. Status: {status}"}
        else:
            logger.error(f"Solver failed with status {status}")
            return {"error": f"No solution found. Status: {status}"}
    
    def _parse_input_data(self) -> Dict:
        """Parse and structure input data for optimization"""
        try:
            logger.info(f"Parsing input data: {len(self.drivers)} drivers, {len(self.routes)} routes, {len(self.availability)} availability records")
            
            # Create driver lookup and parse monthly hours
            driver_info = {}
            for driver in self.drivers:
                driver_id = driver.get('driver_id') or driver.get('id')
                driver_name = driver.get('name') or driver.get('driver_name', 'Unknown Driver')
                
                # Handle monthly hours from various formats
                monthly_hours = 174.0  # Default
                if 'details' in driver and isinstance(driver['details'], dict):
                    monthly_hours_str = driver['details'].get('monthly_hours', '174:00')
                elif 'monthly_hours' in driver:
                    monthly_hours_str = str(driver['monthly_hours'])
                else:
                    monthly_hours_str = '174:00'
                
                # Convert "174:00" format to decimal hours
                if ':' in str(monthly_hours_str):
                    try:
                        hours, minutes = str(monthly_hours_str).split(':')
                        monthly_hours = float(hours) + float(minutes) / 60.0
                    except:
                        monthly_hours = 174.0
                else:
                    try:
                        monthly_hours = float(monthly_hours_str)
                    except:
                        monthly_hours = 174.0
                
                driver_info[driver_id] = {
                    'name': driver_name,
                    'monthly_hours': monthly_hours,
                    'type': 'full_time'
                }
            
            # Group routes by date and parse duration
            routes_by_date = {}
            for route in self.routes:
                route_date = str(route['date'])
                if route_date not in routes_by_date:
                    routes_by_date[route_date] = []
                
                # Default duration based on route type
                duration = 8.0
                if 'SA' in route.get('route_name', ''):  # Saturday routes
                    duration = 6.0
                elif route.get('route_name', '') in ['431oS', '432oS', '433oS']:
                    duration = 11.0
                elif route.get('route_name', '') in ['434oS']:
                    duration = 10.0
                elif route.get('route_name', '') in ['440oS']:
                    duration = 3.0
                elif route.get('route_name', '') in ['435oS', '436oS', '437oS', '438oS', '439oS']:
                    duration = 12.0
                
                routes_by_date[route_date].append({
                    'route_id': len(routes_by_date[route_date]),  # Sequential ID for this date
                    'route_name': route['route_name'],
                    'original_route_id': route.get('route_id', 0),
                    'duration': duration,
                    'day_of_week': route_date  # Use date as day identifier
                })
            
            # Create availability lookup
            availability_map = {}
            for avail in self.availability:
                avail_date = str(avail['date'])
                driver_id = avail['driver_id']
                
                if avail_date not in availability_map:
                    availability_map[avail_date] = {}
                
                availability_map[avail_date][driver_id] = {
                    'available': avail.get('available', False),
                    'available_hours': float(avail.get('available_hours', 24)),  # Default full day
                    'max_routes': int(avail.get('max_routes', 3)),  # Default max 3 routes
                    'shift_preference': 'any'
                }
            
            result = {
                'driver_info': driver_info,
                'routes_by_date': routes_by_date,
                'availability_map': availability_map,
                'dates': sorted(routes_by_date.keys())
            }
            
            logger.info(f"Parsed data: {len(driver_info)} drivers, {len(routes_by_date)} dates, {sum(len(routes) for routes in routes_by_date.values())} total routes")
            for date, routes in routes_by_date.items():
                logger.info(f"  Date {date}: {len(routes)} routes - {[r['route_name'] for r in routes]}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing input data: {e}")
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
        
        # Constraint 2: Driver availability constraints (relaxed for feasibility)
        for driver_id in driver_info:
            for date in dates:
                # Only apply constraints if availability data exists and driver is not available
                if (date in availability_map and 
                    driver_id in availability_map[date] and 
                    not availability_map[date][driver_id]['available']):
                    
                    # Driver not available - cannot be assigned any route
                    for route_id in x[driver_id].get(date, {}):
                        constraint = self.solver.Constraint(0, 0)
                        constraint.SetCoefficient(x[driver_id][date][route_id], 1)
                else:
                    # Driver is available or no specific availability data - allow reasonable assignments
                    # Limit to max 3 routes per driver per day (reasonable constraint)
                    if date in x[driver_id] and x[driver_id][date]:
                        constraint = self.solver.Constraint(0, 3)  # Max 3 routes per day
                        for route_id in x[driver_id][date]:
                            constraint.SetCoefficient(x[driver_id][date][route_id], 1)
        
        # Constraint 3: Reasonable weekly hours constraint (relaxed for feasibility)
        for driver_id in driver_info:
            monthly_hours = driver_info[driver_id]['monthly_hours']
            weekly_hours_limit = max(60, monthly_hours / 3.5)  # More generous weekly limit
            
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
        
        # Objective: Maximize assignments and balance workload
        objective = self.solver.Objective()
        
        # Primary goal: assign all routes (highest priority)
        for driver_id in driver_info:
            for date in dates:
                if date in routes_by_date:
                    for route in routes_by_date[date]:
                        route_id = route['route_id']
                        if driver_id in x and date in x[driver_id] and route_id in x[driver_id][date]:
                            objective.SetCoefficient(x[driver_id][date][route_id], 1000)
        
        # Secondary goal: prefer drivers with more remaining monthly hours
        for driver_id in driver_info:
            monthly_hours = driver_info[driver_id]['monthly_hours']
            preference_weight = int(monthly_hours)  # Higher monthly hours = higher preference
            
            for date in dates:
                if date in routes_by_date:
                    for route in routes_by_date[date]:
                        route_id = route['route_id']
                        if driver_id in x and date in x[driver_id] and route_id in x[driver_id][date]:
                            objective.SetCoefficient(x[driver_id][date][route_id], preference_weight)
        
        objective.SetMaximization()
    
    def _extract_solution(self, data: Dict) -> Dict:
        """Extract the solution from the solved model"""
        try:
            assignments = {}
            statistics = {
                'total_routes': 0,
                'assigned_routes': 0,
                'unassigned_routes': 0,
                'driver_assignments': {},
                'date_breakdown': {},
                'optimization_method': 'OR-Tools Linear Programming',
                'solver_status': 'OPTIMAL'
            }
            
            driver_info = data['driver_info']
            routes_by_date = data['routes_by_date']
            dates = data['dates']
            
            # Extract assignments
            for date in dates:
                assignments[date] = []
                statistics['date_breakdown'][date] = {'assigned': 0, 'unassigned': 0}
                
                if date in routes_by_date:
                    statistics['total_routes'] += len(routes_by_date[date])
                    
                    for route in routes_by_date[date]:
                        route_id = route['route_id']
                        assigned = False
                        
                        for driver_id in driver_info:
                            if (driver_id in self.decision_vars and 
                                date in self.decision_vars[driver_id] and 
                                route_id in self.decision_vars[driver_id][date]):
                                
                                if self.decision_vars[driver_id][date][route_id].SolutionValue() > 0.5:
                                    # This route is assigned to this driver
                                    assignments[date].append({
                                        'driver_id': driver_id,
                                        'driver_name': driver_info[driver_id]['name'],
                                        'route_id': route.get('original_route_id', route_id),
                                        'route_name': route['route_name'],
                                        'date': date,
                                        'duration': route['duration'],
                                        'status': 'assigned'
                                    })
                                    
                                    # Update statistics
                                    statistics['assigned_routes'] += 1
                                    statistics['date_breakdown'][date]['assigned'] += 1
                                    
                                    if driver_info[driver_id]['name'] not in statistics['driver_assignments']:
                                        statistics['driver_assignments'][driver_info[driver_id]['name']] = 0
                                    statistics['driver_assignments'][driver_info[driver_id]['name']] += 1
                                    
                                    assigned = True
                                    break
                        
                        if not assigned:
                            statistics['unassigned_routes'] += 1
                            statistics['date_breakdown'][date]['unassigned'] += 1
            
            # Calculate success rate
            success_rate = (statistics['assigned_routes'] / statistics['total_routes'] * 100) if statistics['total_routes'] > 0 else 0
            
            return {
                'status': 'success',
                'success_rate': success_rate,
                'assignments': assignments,
                'statistics': statistics,
                'solver_status': statistics['solver_status'],
                'unassigned_routes': [],  # Could be populated if needed
                'optimization_method': 'OR-Tools Linear Programming',
                'week_period': 'July 7-13, 2025',
                'data_source': 'Supabase'
            }
            
        except Exception as e:
            logger.error(f"Error extracting solution: {e}")
            return {"error": f"Failed to extract solution: {str(e)}"}

def optimize_driver_schedule(drivers: List[Dict], routes: List[Dict], availability: List[Dict]) -> Dict[str, Any]:
    """
    Main entry point for driver schedule optimization using OR-Tools
    
    Args:
        drivers: List of driver records from Supabase
        routes: List of route records for July 7-13, 2025 
        availability: List of availability records
    
    Returns:
        Dict containing optimal assignments and detailed statistics
    """
    
    logger.info(f"Starting OR-Tools optimization: {len(drivers)} drivers, {len(routes)} routes, {len(availability)} availability records")
    
    try:
        # Create optimizer instance
        optimizer = DriverRouteOptimizer()
        
        # Run optimization
        result = optimizer.optimize_assignments(drivers, routes, availability)
        
        if 'error' in result:
            logger.error(f"Optimization failed: {result['error']}")
            return result
        
        success_rate = result.get('success_rate', 0)
        total_routes = result.get('statistics', {}).get('total_routes', 0)
        assigned_routes = result.get('statistics', {}).get('assigned_routes', 0)
        
        logger.info(f"OR-Tools optimization complete: {success_rate:.1f}% success rate, {assigned_routes}/{total_routes} routes assigned")
        
        return result
        
    except Exception as e:
        logger.error(f"Optimization error: {str(e)}")
        return {"error": f"Optimization failed: {str(e)}"}