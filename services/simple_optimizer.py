"""
Pure OR-Tools Driver Route Assignment Optimization
Uses linear programming to optimize driver assignments considering:
- Driver availability per date
- Monthly hour limits (remaining hours)  
- Route duration requirements
- Optimal workload distribution
"""

import logging
from typing import Dict, List, Any
from datetime import date
import json
from ortools.linear_solver import pywraplp

logger = logging.getLogger(__name__)

def optimize_driver_schedule(drivers: List[Dict], routes: List[Dict], availability: List[Dict]) -> Dict[str, Any]:
    """
    OR-Tools Linear Programming optimization for driver scheduling
    
    Args:
        drivers: List with driver_id, name, monthly_hours_limit (remaining hours)
        routes: List with route_id, date, route_name, details.duration (route hours) 
        availability: List with driver_id, date, available (boolean)
    
    Returns:
        Dict containing optimal assignments or error
    """
    
    logger.info(f"OR-Tools optimization starting: {len(drivers)} drivers, {len(routes)} routes, {len(availability)} availability records")
    
    # Debug input data structure
    if drivers:
        logger.info(f"Sample driver: {drivers[0]}")
    if routes:
        logger.info(f"Sample route: {routes[0]}")  
    if availability:
        logger.info(f"Sample availability: {availability[0]}")
    
    try:
        # Create SCIP solver
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver:
            error_msg = "Failed to create OR-Tools SCIP solver"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # Parse input data with correct structure
        driver_info = {}
        for driver in drivers:
            logger.info(f"Processing driver type: {type(driver)}, value: {driver}")
            if isinstance(driver, str):
                logger.error(f"Driver is string instead of dict: {driver}")
                continue
            driver_id = driver['driver_id']
            driver_info[driver_id] = {
                'name': driver['name'],
                'monthly_hours_remaining': float(driver.get('monthly_hours_limit', 174))  # Remaining hours
            }
        
        # Parse routes with durations
        routes_by_date = {}
        for route in routes:
            logger.info(f"Processing route type: {type(route)}, value: {route}")
            if isinstance(route, str):
                logger.error(f"Route is string instead of dict: {route}")
                continue
            route_date = str(route['date'])
            if route_date not in routes_by_date:
                routes_by_date[route_date] = []
            
            # Extract duration from details JSONB field (could be string or dict)
            details = route.get('details', {})
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except:
                    details = {}
            
            duration_str = details.get('duration', '8:00')
            if isinstance(duration_str, str) and ':' in duration_str:
                hours, minutes = duration_str.split(':')
                duration = float(hours) + float(minutes) / 60.0
            else:
                duration = 8.0  # Default
            
            routes_by_date[route_date].append({
                'route_id': route['route_id'],
                'route_name': route['route_name'],
                'duration': duration
            })
        
        # Parse availability 
        availability_map = {}
        for avail in availability:
            date_str = str(avail['date'])
            driver_id = avail['driver_id']
            
            if date_str not in availability_map:
                availability_map[date_str] = {}
            
            availability_map[date_str][driver_id] = avail.get('available', False)
        
        dates = sorted(routes_by_date.keys())
        logger.info(f"Parsed data: {len(driver_info)} drivers, {len(dates)} dates, {sum(len(routes) for routes in routes_by_date.values())} total routes")
        
        # Create decision variables: x[driver_id][date][route_id] = 1 if assigned
        x = {}
        for driver_id in driver_info:
            x[driver_id] = {}
            for date in dates:
                x[driver_id][date] = {}
                if date in routes_by_date:
                    for route in routes_by_date[date]:
                        route_id = route['route_id']
                        x[driver_id][date][route_id] = solver.BoolVar(f'x_{driver_id}_{date}_{route_id}')
        
        logger.info(f"Created decision variables for {len(driver_info)} drivers across {len(dates)} dates")
        
        # CONSTRAINT 1: Each route must be assigned to exactly one driver
        for date in dates:
            if date in routes_by_date:
                for route in routes_by_date[date]:
                    route_id = route['route_id']
                    constraint = solver.Constraint(1, 1, f'route_{route_id}_date_{date}')
                    
                    for driver_id in driver_info:
                        if driver_id in x and date in x[driver_id] and route_id in x[driver_id][date]:
                            constraint.SetCoefficient(x[driver_id][date][route_id], 1)
        
        # CONSTRAINT 2: Driver availability constraints
        for driver_id in driver_info:
            for date in dates:
                if date in availability_map and driver_id in availability_map[date]:
                    if not availability_map[date][driver_id]:
                        # Driver not available on this date - cannot assign any routes
                        for route_id in x[driver_id].get(date, {}):
                            constraint = solver.Constraint(0, 0, f'unavailable_{driver_id}_{date}_{route_id}')
                            constraint.SetCoefficient(x[driver_id][date][route_id], 1)
        
        # CONSTRAINT 3: Monthly hours limit constraint
        for driver_id in driver_info:
            monthly_limit = driver_info[driver_id]['monthly_hours_remaining']
            constraint = solver.Constraint(0, monthly_limit, f'monthly_hours_{driver_id}')
            
            for date in dates:
                if date in routes_by_date:
                    for route in routes_by_date[date]:
                        route_id = route['route_id']
                        if driver_id in x and date in x[driver_id] and route_id in x[driver_id][date]:
                            constraint.SetCoefficient(x[driver_id][date][route_id], route['duration'])
        
        # CONSTRAINT 4: Reasonable daily workload (max 16 hours per day)
        for driver_id in driver_info:
            for date in dates:
                if date in routes_by_date:
                    constraint = solver.Constraint(0, 16, f'daily_hours_{driver_id}_{date}')
                    for route in routes_by_date[date]:
                        route_id = route['route_id']
                        if driver_id in x and date in x[driver_id] and route_id in x[driver_id][date]:
                            constraint.SetCoefficient(x[driver_id][date][route_id], route['duration'])
        
        # OBJECTIVE: Maximize total assignments with preference for drivers with more remaining hours
        objective = solver.Objective()
        
        for driver_id in driver_info:
            monthly_remaining = driver_info[driver_id]['monthly_hours_remaining']
            weight = 1000 + int(monthly_remaining)  # Higher remaining hours = higher weight
            
            for date in dates:
                if date in routes_by_date:
                    for route in routes_by_date[date]:
                        route_id = route['route_id']
                        if driver_id in x and date in x[driver_id] and route_id in x[driver_id][date]:
                            objective.SetCoefficient(x[driver_id][date][route_id], weight)
        
        objective.SetMaximization()
        logger.info("Constraints and objective set. Starting solver...")
        
        # Solve
        status = solver.Solve()
        
        logger.info(f"Solver finished with status: {status}")
        
        if status == pywraplp.Solver.OPTIMAL:
            logger.info("Found optimal solution")
            
            # Extract solution
            assignments = {}
            statistics = {
                'total_routes': sum(len(routes) for routes in routes_by_date.values()),
                'assigned_routes': 0,
                'unassigned_routes': 0,
                'driver_assignments': {},
                'date_breakdown': {},
                'optimization_method': 'OR-Tools Linear Programming (SCIP)',
                'solver_status': 'OPTIMAL',
                'total_drivers': len(drivers),
                'active_drivers': 0,
                'total_hours_assigned': 0.0
            }
            
            for date in dates:
                assignments[date] = []
                statistics['date_breakdown'][date] = {'assigned': 0, 'unassigned': 0}
                
                if date in routes_by_date:
                    for route in routes_by_date[date]:
                        route_id = route['route_id']
                        assigned = False
                        
                        for driver_id in driver_info:
                            if (driver_id in x and date in x[driver_id] and 
                                route_id in x[driver_id][date] and 
                                x[driver_id][date][route_id].solution_value() > 0.5):
                                
                                assignments[date].append({
                                    'driver_id': driver_id,
                                    'driver_name': driver_info[driver_id]['name'],
                                    'route_id': route_id,
                                    'route_name': route['route_name'],
                                    'date': date,
                                    'duration': route['duration'],
                                    'status': 'assigned'
                                })
                                
                                statistics['assigned_routes'] += 1
                                statistics['date_breakdown'][date]['assigned'] += 1
                                statistics['total_hours_assigned'] += route['duration']
                                
                                if driver_info[driver_id]['name'] not in statistics['driver_assignments']:
                                    statistics['driver_assignments'][driver_info[driver_id]['name']] = 0
                                statistics['driver_assignments'][driver_info[driver_id]['name']] += 1
                                
                                assigned = True
                                break
                        
                        if not assigned:
                            statistics['unassigned_routes'] += 1
                            statistics['date_breakdown'][date]['unassigned'] += 1
            
            statistics['active_drivers'] = len(statistics['driver_assignments'])
            success_rate = (statistics['assigned_routes'] / statistics['total_routes'] * 100) if statistics['total_routes'] > 0 else 0
            
            logger.info(f"OR-Tools optimization complete: {success_rate:.1f}% success rate, {statistics['assigned_routes']}/{statistics['total_routes']} routes assigned")
            
            return {
                'status': 'success',
                'success_rate': success_rate,
                'assignments': assignments,
                'statistics': statistics,
                'solver_status': 'OPTIMAL',
                'unassigned_routes': [],
                'optimization_method': 'OR-Tools Linear Programming (SCIP)',
                'week_period': 'July 7-13, 2025',
                'data_source': 'Supabase PostgreSQL'
            }
            
        elif status == pywraplp.Solver.INFEASIBLE:
            error_msg = "Problem is INFEASIBLE - constraints cannot be satisfied with current driver availability and hour limits"
            logger.error(error_msg)
            return {"error": error_msg}
            
        elif status == pywraplp.Solver.UNBOUNDED:
            error_msg = "Problem is UNBOUNDED - objective can increase infinitely"
            logger.error(error_msg)
            return {"error": error_msg}
            
        else:
            error_msg = f"Solver failed with status {status} (ABNORMAL=4, NOT_SOLVED=6)"
            logger.error(error_msg)
            return {"error": error_msg}
            
    except Exception as e:
        error_msg = f"OR-Tools optimization crashed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"error": error_msg}