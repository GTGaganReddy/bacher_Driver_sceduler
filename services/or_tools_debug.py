"""
Debug version of your original OR-Tools algorithm to capture exact errors
"""

import logging
from typing import Dict, List, Any
from datetime import date
import json
from ortools.linear_solver import pywraplp

logger = logging.getLogger(__name__)

def debug_or_tools_optimization(drivers: List[Dict], routes: List[Dict], availability: List[Dict]) -> Dict[str, Any]:
    """
    Debug your original OR-Tools algorithm with detailed error capture
    """
    
    logger.info(f"=== DEBUG OR-TOOLS INPUT ===")
    logger.info(f"Drivers ({len(drivers)}):")
    for i, driver in enumerate(drivers[:3]):  # First 3 drivers
        logger.info(f"  Driver {i}: {driver}")
    
    logger.info(f"Routes ({len(routes)}):")
    for i, route in enumerate(routes[:5]):  # First 5 routes
        logger.info(f"  Route {i}: {route}")
        
    logger.info(f"Availability ({len(availability)}):")
    for i, avail in enumerate(availability[:5]):  # First 5 availability records
        logger.info(f"  Availability {i}: {avail}")
    
    try:
        # Create solver
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver:
            error_msg = "Could not create SCIP solver"
            logger.error(f"=== SOLVER CREATION ERROR: {error_msg} ===")
            return {"error": error_msg}
        
        logger.info("✅ Solver created successfully")
        
        # Parse input data
        logger.info("=== PARSING INPUT DATA ===")
        
        # Create driver lookup
        driver_info = {}
        for driver in drivers:
            driver_id = driver.get('driver_id') or driver.get('id')
            driver_name = driver.get('name') or driver.get('driver_name', 'Unknown Driver')
            
            driver_info[driver_id] = {
                'name': driver_name,
                'monthly_hours': 174.0
            }
            
        logger.info(f"✅ Parsed {len(driver_info)} drivers")
        
        # Group routes by date
        routes_by_date = {}
        for route in routes:
            route_date = str(route['date'])
            if route_date not in routes_by_date:
                routes_by_date[route_date] = []
            
            routes_by_date[route_date].append({
                'route_id': len(routes_by_date[route_date]),
                'route_name': route['route_name'],
                'original_route_id': route.get('route_id', 0),
                'duration': 8.0
            })
        
        dates = sorted(routes_by_date.keys())
        logger.info(f"✅ Parsed routes for dates: {dates}")
        
        # Create decision variables
        logger.info("=== CREATING DECISION VARIABLES ===")
        x = {}
        var_count = 0
        
        for driver_id in driver_info:
            x[driver_id] = {}
            for date in dates:
                x[driver_id][date] = {}
                if date in routes_by_date:
                    for route in routes_by_date[date]:
                        route_id = route['route_id']
                        var_name = f'x_{driver_id}_{date}_{route_id}'
                        x[driver_id][date][route_id] = solver.BoolVar(var_name)
                        var_count += 1
        
        logger.info(f"✅ Created {var_count} decision variables")
        
        # Add constraints
        logger.info("=== ADDING CONSTRAINTS ===")
        constraint_count = 0
        
        # Constraint 1: Each route must be assigned to exactly one driver
        for date in dates:
            if date in routes_by_date:
                for route in routes_by_date[date]:
                    route_id = route['route_id']
                    constraint = solver.Constraint(1, 1)
                    constraint_count += 1
                    
                    for driver_id in driver_info:
                        if driver_id in x and date in x[driver_id] and route_id in x[driver_id][date]:
                            constraint.SetCoefficient(x[driver_id][date][route_id], 1)
        
        logger.info(f"✅ Added {constraint_count} route assignment constraints")
        
        # Set objective
        logger.info("=== SETTING OBJECTIVE ===")
        objective = solver.Objective()
        obj_coeffs = 0
        
        for driver_id in driver_info:
            for date in dates:
                if date in routes_by_date:
                    for route in routes_by_date[date]:
                        route_id = route['route_id']
                        if driver_id in x and date in x[driver_id] and route_id in x[driver_id][date]:
                            objective.SetCoefficient(x[driver_id][date][route_id], 1000)
                            obj_coeffs += 1
        
        objective.SetMaximization()
        logger.info(f"✅ Set objective with {obj_coeffs} coefficients")
        
        # Solve
        logger.info("=== SOLVING ===")
        status = solver.Solve()
        
        logger.info(f"Solver status: {status}")
        logger.info(f"Status codes: OPTIMAL=0, FEASIBLE=1, INFEASIBLE=2, UNBOUNDED=3, ABNORMAL=4, NOT_SOLVED=6")
        
        if status == pywraplp.Solver.OPTIMAL:
            logger.info("✅ Found optimal solution")
            
            # Extract solution
            logger.info("=== EXTRACTING SOLUTION ===")
            assignments = {}
            total_assigned = 0
            
            for date in dates:
                assignments[date] = []
                
                if date in routes_by_date:
                    for route in routes_by_date[date]:
                        route_id = route['route_id']
                        
                        for driver_id in driver_info:
                            if (driver_id in x and date in x[driver_id] and route_id in x[driver_id][date]):
                                try:
                                    solution_value = x[driver_id][date][route_id].SolutionValue()
                                    if solution_value > 0.5:
                                        assignments[date].append({
                                            'driver_id': driver_id,
                                            'driver_name': driver_info[driver_id]['name'],
                                            'route_id': route.get('original_route_id', route_id),
                                            'route_name': route['route_name'],
                                            'date': date,
                                            'duration': route['duration'],
                                            'status': 'assigned'
                                        })
                                        total_assigned += 1
                                        break
                                except Exception as extract_error:
                                    logger.error(f"❌ SOLUTION EXTRACTION ERROR: {extract_error}")
                                    logger.error(f"Variable: {var_name}, Driver: {driver_id}, Date: {date}, Route: {route_id}")
                                    return {"error": f"Solution extraction failed: {str(extract_error)}"}
            
            logger.info(f"✅ Extracted {total_assigned} assignments")
            
            return {
                'status': 'success',
                'success_rate': (total_assigned / len(routes)) * 100,
                'assignments': assignments,
                'statistics': {
                    'total_routes': len(routes),
                    'assigned_routes': total_assigned,
                    'optimization_method': 'OR-Tools SCIP Solver',
                    'solver_status': 'OPTIMAL'
                }
            }
            
        elif status == pywraplp.Solver.INFEASIBLE:
            error_msg = f"Problem is INFEASIBLE - constraints cannot be satisfied"
            logger.error(f"❌ {error_msg}")
            return {"error": error_msg}
        else:
            error_msg = f"Solver failed with status {status}"
            logger.error(f"❌ {error_msg}")
            return {"error": error_msg}
            
    except Exception as e:
        logger.error(f"❌ UNEXPECTED ERROR: {str(e)}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}