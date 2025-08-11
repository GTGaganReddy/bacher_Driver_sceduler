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
            
            # If all_drivers and all_dates provided, create complete driver grid
            if all_drivers and all_dates:
                # Create assignment lookup for quick access
                assignment_lookup = {}
                unavailable_lookup = {}
                
                for date_key, date_assignments in assignments.items():
                    if isinstance(date_assignments, dict):
                        for route_name, assignment_details in date_assignments.items():
                            driver_name = assignment_details.get('driver_name', '')
                            
                            if driver_name not in assignment_lookup:
                                assignment_lookup[driver_name] = {}
                                unavailable_lookup[driver_name] = {}
                            
                            # Check if this is an "F" entry (unavailable driver)
                            if route_name.startswith('F_') and assignment_details.get('status') == 'unavailable':
                                unavailable_lookup[driver_name][date_key] = {
                                    "route": "F",
                                    "hour": "0:00"
                                }
                            elif assignment_details.get('status') == 'assigned':
                                # Regular route assignment
                                duration = assignment_details.get('duration_hours', 8.0)
                                hour_str = f"{int(duration)}:{int((duration % 1) * 60):02d}"
                                
                                assignment_lookup[driver_name][date_key] = {
                                    "route": route_name,
                                    "hour": hour_str
                                }
                
                # Create entries for ALL drivers on ALL dates (assigned, unavailable "F", or blank)
                for driver in all_drivers:
                    driver_name = driver.get('name', '')
                    
                    for date_key in all_dates:
                        if driver_name in assignment_lookup and date_key in assignment_lookup[driver_name]:
                            # Driver has route assignment on this date
                            assignment = assignment_lookup[driver_name][date_key]
                            driver_data = {
                                "driver": driver_name,
                                "route": assignment["route"],
                                "hour": assignment["hour"],
                                "remaining_hour": "0:00",
                                "date": date_key,
                                "status": "update"
                            }
                        elif driver_name in unavailable_lookup and date_key in unavailable_lookup[driver_name]:
                            # Driver is unavailable on this date - send "F" entry
                            unavailable_info = unavailable_lookup[driver_name][date_key]
                            driver_data = {
                                "driver": driver_name,
                                "route": "F",
                                "hour": "0:00",
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
            
            logger.info(f"Sending {total_entries} total entries to Google Sheets via GCF ({assigned_entries} assigned, {f_entries} F entries, {blank_entries} blank)")
            
            # Debug: Show sample entries for unavailable drivers
            sample_entries = []
            for driver in ["Fröhlacher, Hubert", "Genäuß, Thomas"][:2]:
                driver_entries = [d for d in drivers_payload if d["driver"] == driver][:2]
                sample_entries.extend(driver_entries)
            
            if sample_entries:
                logger.info(f"Sample entries for test drivers: {sample_entries}")
            
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
