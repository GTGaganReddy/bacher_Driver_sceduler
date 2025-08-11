import httpx
import logging
from typing import List, Dict, Any
from config.settings import settings
from schemas.models import Assignment

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self):
        self.gcf_url = settings.GCF_URL
    
    async def update_sheet(self, optimization_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send optimization results to your Google Cloud Function for sheet update
        Converts optimization format to your GCF driver assignment format
        """
        try:
            # Extract assignments from optimization result
            assignments = optimization_result.get('assignments', {})
            drivers_payload = []
            
            # Convert optimization results to your GCF format
            # Handle both dict (route_name -> details) and list formats
            for date_key, date_assignments in assignments.items():
                if isinstance(date_assignments, dict):
                    # New format: route_name -> assignment_details
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
                elif isinstance(date_assignments, list):
                    # Legacy list format
                    for assignment in date_assignments:
                        duration = assignment.get('duration_hours', 8.0)
                        hour_str = f"{int(duration)}:{int((duration % 1) * 60):02d}"
                        
                        driver_data = {
                            "driver": assignment.get('driver_name', ''),
                            "route": assignment.get('route_name', ''),
                            "hour": hour_str,
                            "remaining_hour": "0:00",
                            "date": assignment.get('date', date_key),
                            "status": "update"
                        }
                        drivers_payload.append(driver_data)
            
            payload = {"drivers": drivers_payload}
            
            logger.info(f"Sending {len(drivers_payload)} driver assignments to Google Sheets via GCF")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.gcf_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info("Successfully updated Google Sheets")
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
