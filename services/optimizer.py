from ortools.sat.python import cp_model
from datetime import date, timedelta
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SchedulingOptimizer:
    def __init__(self):
        self.model = None
        self.solver = None
    
    def optimize_assignments(self, drivers: List[Dict], routes: List[Dict], availability: List[Dict], week_start: date) -> List[Dict]:
        """
        Optimize driver-route assignments using OR-Tools CP-SAT solver
        """
        try:
            # Create the model
            model = cp_model.CpModel()
            
            # Prepare data structures
            driver_ids = [d['driver_id'] for d in drivers]
            driver_names = {d['driver_id']: d['name'] for d in drivers}
            
            # Group routes by date
            routes_by_date = {}
            for route in routes:
                route_date = route['date']
                if route_date not in routes_by_date:
                    routes_by_date[route_date] = []
                routes_by_date[route_date].append(route)
            
            # Create availability lookup
            availability_lookup = {}
            for avail in availability:
                key = (avail['driver_id'], avail['date'])
                availability_lookup[key] = avail['available']
            
            # Generate week dates
            week_dates = [week_start + timedelta(days=i) for i in range(7)]
            
            # Create decision variables
            assignments = {}
            for day_idx, current_date in enumerate(week_dates):
                if current_date in routes_by_date:
                    for route in routes_by_date[current_date]:
                        for driver_id in driver_ids:
                            # Check if driver is available on this date
                            is_available = availability_lookup.get((driver_id, current_date), True)
                            
                            if is_available:
                                var_name = f"assign_d{driver_id}_r{route['route_id']}_day{day_idx}"
                                assignments[(driver_id, route['route_id'], day_idx)] = model.NewBoolVar(var_name)
            
            # Constraints
            
            # 1. Each route must be assigned to exactly one driver
            for day_idx, current_date in enumerate(week_dates):
                if current_date in routes_by_date:
                    for route in routes_by_date[current_date]:
                        model.Add(
                            sum(assignments.get((driver_id, route['route_id'], day_idx), 0) 
                                for driver_id in driver_ids) == 1
                        )
            
            # 2. Each driver can be assigned to at most one route per day
            for day_idx, current_date in enumerate(week_dates):
                if current_date in routes_by_date:
                    for driver_id in driver_ids:
                        daily_routes = [route['route_id'] for route in routes_by_date[current_date]]
                        model.Add(
                            sum(assignments.get((driver_id, route_id, day_idx), 0) 
                                for route_id in daily_routes) <= 1
                        )
            
            # 3. Balance workload across drivers (optional objective)
            # Create variables for total assignments per driver
            driver_totals = {}
            for driver_id in driver_ids:
                driver_totals[driver_id] = model.NewIntVar(0, len(routes), f"total_d{driver_id}")
                model.Add(
                    driver_totals[driver_id] == sum(
                        assignments.get((driver_id, route['route_id'], day_idx), 0)
                        for day_idx, current_date in enumerate(week_dates)
                        if current_date in routes_by_date
                        for route in routes_by_date[current_date]
                    )
                )
            
            # Objective: Minimize the maximum workload difference
            max_workload = model.NewIntVar(0, len(routes), "max_workload")
            min_workload = model.NewIntVar(0, len(routes), "min_workload")
            
            for driver_id in driver_ids:
                model.Add(max_workload >= driver_totals[driver_id])
                model.Add(min_workload <= driver_totals[driver_id])
            
            model.Minimize(max_workload - min_workload)
            
            # Solve the model
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = 30.0
            
            status = solver.Solve(model)
            
            # Process results
            result_assignments = []
            
            if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                for day_idx, current_date in enumerate(week_dates):
                    if current_date in routes_by_date:
                        for route in routes_by_date[current_date]:
                            for driver_id in driver_ids:
                                key = (driver_id, route['route_id'], day_idx)
                                if key in assignments and solver.Value(assignments[key]) == 1:
                                    result_assignments.append({
                                        "driver": driver_names[driver_id],
                                        "driver_id": driver_id,
                                        "route": route['route_name'],
                                        "route_id": route['route_id'],
                                        "date": current_date.isoformat(),
                                        "hour": "08:00",  # Default start time
                                        "remaining_hour": "16:00",  # Default end time
                                        "status": "assigned"
                                    })
                
                logger.info(f"Optimization completed successfully. Status: {solver.StatusName(status)}")
                logger.info(f"Generated {len(result_assignments)} assignments")
                
            else:
                logger.warning(f"Optimization failed. Status: {solver.StatusName(status)}")
                # Return basic assignments without optimization
                result_assignments = self._create_basic_assignments(drivers, routes, availability, week_start)
            
            return result_assignments
            
        except Exception as e:
            logger.error(f"Error in optimization: {e}")
            # Fallback to basic assignment strategy
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
            availability_lookup[key] = avail['available']
        
        for route in routes:
            assigned = False
            attempts = 0
            
            while not assigned and attempts < len(drivers):
                driver = drivers[driver_index % len(drivers)]
                is_available = availability_lookup.get((driver['driver_id'], route['date']), True)
                
                if is_available:
                    assignments.append({
                        "driver": driver['name'],
                        "driver_id": driver['driver_id'],
                        "route": route['route_name'],
                        "route_id": route['route_id'],
                        "date": route['date'].isoformat(),
                        "hour": "08:00",
                        "remaining_hour": "16:00",
                        "status": "assigned"
                    })
                    assigned = True
                
                driver_index += 1
                attempts += 1
            
            if not assigned:
                logger.warning(f"Could not assign route {route['route_name']} on {route['date']}")
        
        return assignments
