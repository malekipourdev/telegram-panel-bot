import httpx
import logging
from config import settings
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class PanelAPIClient:
    def __init__(self):
        self.base_url = settings.PANEL_BASE_URL
        self.token = settings.PANEL_API_TOKEN
        self.timeout = settings.API_TIMEOUT
        self.headers = self._build_headers()
    
    def _build_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "TelegramPanelBot/1.0"
        }
    
    async def get_clients_list(self) -> Dict[str, Any]:
        url = f"{self.base_url}/panel/api/clients/list"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching clients: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching clients: {e}")
            raise
    
    async def create_client(self, email: str, total_bytes: int, inbound_id: int = 1) -> Dict[str, Any]:
        """
        Creates a client on 3X-UI panel and automatically fetches its genuine server-generated UUID.
        Returns a dict with 'success' and 'uuid'.
        """
        url = f"{self.base_url}/panel/api/clients/add"
        
        # Exact payload structure from 3X-UI documentation (No custom 'id' key allowed)
        payload = {
            "client": {
                "email": email,
                "totalGB": total_bytes,
                "expiryTime": 0,
                "tgId": 0,
                "limitIp": 0,
                "enable": True
            },
            "inboundIds": [inbound_id]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                result = response.json()
                
                if result.get("success"):
                    logger.info(f"Client {email} added successfully. Fetching panel list to sync UUID...")
                    
                    # Call the existing method to fetch all clients from the panel
                    clients_data = await self.get_clients_list()
                    clients_list = clients_data.get("obj", [])
                    
                    # Look for the exact match based on our unique email
                    actual_uuid = None
                    for c in clients_list:
                        if isinstance(c, dict) and c.get("email") == email:
                            actual_uuid = c.get("subId") # In list response, 'subId' holds the genuine UUID string
                            break
                    
                    if actual_uuid:
                        return {"success": True, "uuid": actual_uuid}
                    else:
                        logger.error(f"Could not find newly created client {email} in the panel clients list.")
                        return {"success": False, "msg": "Could not locate the generated UUID on panel."}
                else:
                    return {"success": False, "msg": result.get("msg", "Unknown panel response error")}
                    
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during client creation process: {e}")
            return {"success": False, "msg": f"HTTP Error: {str(e)}"}
        except Exception as e:
            logger.error(f"Internal exception during client creation process: {e}")
            return {"success": False, "msg": f"Internal Error: {str(e)}"}