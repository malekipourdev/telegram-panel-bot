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
    
    async def create_client(self, email: str, total_bytes: int, client_uuid: str, inbound_id: int = 1) -> Dict[str, Any]:
        """
        Sends an asynchronous POST request to the 3X-UI panel.
        Passes the locally generated UUID so the panel adopts it instead of creating a new one.
        """
        url = f"{self.base_url}/panel/api/clients/add"
        
        payload = {
            "client": {
                "id": client_uuid,      # <=== WE PASS OUR UUID HERE AS REVEALED BY DOCS
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
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating client: {e}")
            return {"success": False, "msg": f"HTTP Error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error creating client: {e}")
            return {"success": False, "msg": f"Internal Error: {str(e)}"}