import httpx
import logging
from typing import List, Dict, Any
from config.settings import settings
from schemas.models import Assignment

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self):
        self.gcf_url = settings.GCF_URL
    
    async def update_sheet(self, optimization_result: Dict[str, Any], all_drivers: List[Dict] = None, all_dates: List[str] = None) -> Dict[str, Any]:
        """
        Send optimization results to your Google Cloud Function for sheet update
        Sends ALL drivers (including unassigned ones) to completely overwrite the sheet
        """
        try:
            assignments = optimization_result.get('assignments', {})
            drivers_payload = []
            
            # Debug: Log the structure of optimization result
            logger.info(f"Optimization result keys: {list(optimization_result.keys())}")
            logger.info(f"Assignments keys: {list(assignments.keys())}")
            if assignments:
                first_date = list(assignments.keys())[0]
                logger.info(f"Sample date '{first_date}' structure: {assignments[first_date]}")
                if isinstance(assignments[first_date], dict) and assignments[first_date]:
                    first_route = list(assignments[first_date].keys())[0]
                    logger.info(f"Sample route '{first_route}' details: {assignments[first_date][first_route]}")
            else:
                logger.warning("No assignments found in optimization result")
            
            # If all_drivers and all_dates provided, create complete driver grid
            if all_drivers and all_dates:
                # Create assignment lookup for quick access
                assignment_lookup = {}
                
                # First pass: collect all assignments and F entries
                for date_key, date_assignments in assignments.items():
                    if isinstance(date_assignments, dict):
                        for route_name, assignment_details in date_assignments.items():
                            driver_name = assignment_details.get('driver_name', '')
                            
                            if driver_name not in assignment_lookup:
                                assignment_lookup[driver_name] = {}
                            
                            if route_name.startswith('F_') and assignment_details.get('status') == 'unavailable':
                                # F entry for unavailable driver
                                assignment_lookup[driver_name][date_key] = {
                                    "route": "F",
                                    "hour": "0:00",
                                    "type": "unavailable"
                                }
                            elif assignment_details.get('status') == 'assigned':
                                # Regular route assignment
                                duration = assignment_details.get('duration_hours', 8.0)
                                hour_str = f"{int(duration)}:{int((duration % 1) * 60):02d}"
                                
                                # Handle multiple route assignments per driver per day
                                if date_key in assignment_lookup[driver_name]:
                                    # Driver already has assignment for this date - combine routes and hours
                                    existing = assignment_lookup[driver_name][date_key]
                                    if existing["type"] == "assigned":
                                        # Combine route names and add hours
                                        combined_route = f"{existing['route']},{route_name}"
                                        existing_hours = float(existing["hour"].split(":")[0]) + float(existing["hour"].split(":")[1])/60
                                        new_hours = existing_hours + duration
                                        combined_hour_str = f"{int(new_hours)}:{int((new_hours % 1) * 60):02d}"
                                        
                                        assignment_lookup[driver_name][date_key] = {
                                            "route": combined_route,
                                            "hour": combined_hour_str,
                                            "type": "assigned"
                                        }
                                    else:
                                        # Replace F entry with route assignment
                                        assignment_lookup[driver_name][date_key] = {
                                            "route": route_name,
                                            "hour": hour_str,
                                            "type": "assigned"
                                        }
                                else:
                                    # First assignment for this driver on this date
                                    assignment_lookup[driver_name][date_key] = {
                                        "route": route_name,
                                        "hour": hour_str,
                                        "type": "assigned"
                                    }
                
                # Create entries for ALL drivers on ALL dates (assigned, unavailable "F", or blank)
                for driver in all_drivers:
                    driver_name = driver.get('name', '')
                    
                    for date_key in all_dates:
                        if driver_name in assignment_lookup and date_key in assignment_lookup[driver_name]:
                            # Driver has an assignment (either route or F) on this date
                            assignment = assignment_lookup[driver_name][date_key]
                            driver_data = {
                                "driver": driver_name,
                                "route": assignment["route"],
                                "hour": assignment["hour"],
                                "remaining_hour": "0:00",
                                "date": date_key,
                                "status": "update"
                            }
                        else:
                            # Driver has NO assignment on this date - send blank entry
                            driver_data = {
                                "driver": driver_name,
                                "route": "",
                                "hour": "",
                                "remaining_hour": "0:00", 
                                "date": date_key,
                                "status": "update"
                            }
                        
                        drivers_payload.append(driver_data)
            
            else:
                # Fallback to original logic if driver/date lists not provided
                for date_key, date_assignments in assignments.items():
                    if isinstance(date_assignments, dict):
                        for route_name, assignment_details in date_assignments.items():
                            duration = assignment_details.get('duration_hours', 8.0)
                            hour_str = f"{int(duration)}:{int((duration % 1) * 60):02d}"
                            
                            driver_data = {
                                "driver": assignment_details.get('driver_name', ''),
                                "route": route_name,
                                "hour": hour_str,
                                "remaining_hour": "0:00",
                                "date": date_key,
                                "status": "update"
                            }
                            drivers_payload.append(driver_data)
            
            payload = {"drivers": drivers_payload}
            
            total_entries = len(drivers_payload)
            assigned_entries = len([d for d in drivers_payload if d["route"] and d["route"] != "F"])
            f_entries = len([d for d in drivers_payload if d["route"] == "F"])
            blank_entries = len([d for d in drivers_payload if not d["route"]])
            
            # Debug: Show distribution of assigned routes
            unique_routes = set([d["route"] for d in drivers_payload if d["route"] and d["route"] != "F"])
            unique_drivers_with_routes = set([d["driver"] for d in drivers_payload if d["route"] and d["route"] != "F"])
            
            logger.info(f"Sending {total_entries} total entries to Google Sheets via GCF ({assigned_entries} assigned, {f_entries} F entries, {blank_entries} blank)")
            logger.info(f"Unique routes in payload: {len(unique_routes)} ({list(unique_routes)[:5]}...)")
            logger.info(f"Unique drivers with assignments: {len(unique_drivers_with_routes)} ({list(unique_drivers_with_routes)[:3]}...)")
            
            # Debug: Show sample entries for assigned drivers
            sample_entries = []
            assigned_drivers = set([d["driver"] for d in drivers_payload if d["route"] and d["route"] != "F"])
            for driver in list(assigned_drivers)[:3]:  # Show first 3 assigned drivers
                driver_entries = [d for d in drivers_payload if d["driver"] == driver and d["route"]][:2]
                sample_entries.extend(driver_entries)
            
            if sample_entries:
                logger.info(f"Sample assigned entries: {sample_entries}")
            else:
                logger.warning("No assigned entries found in payload - this may indicate an issue with assignment data conversion")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.gcf_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info("Successfully updated Google Sheets with complete driver grid")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error updating Google Sheets: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to update Google Sheets: HTTP {e.response.status_code}")
        
        except httpx.RequestError as e:
            logger.error(f"Request error updating Google Sheets: {e}")
            raise Exception(f"Failed to connect to Google Sheets service: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error updating Google Sheets: {e}")
            raise Exception(f"Failed to update Google Sheets: {str(e)}")
    
    async def test_connection(self) -> bool:
        """
        Test connection to Google Cloud Function
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.gcf_url)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Google Sheets connection test failed: {e}")
            return False
