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
        url = f"{self.base_url}/panel/api/clients/add"
        
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
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating client: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating client: {e}")
            raise

    @staticmethod
    async def add_client(self, email: str, total_bytes: int, inbound_id: int = 1) -> dict:
        """
        Sends an asynchronous POST request to the 3X-UI panel to register a new client config.
        """
        add_url = f"{self.base_url}/panel/api/clients/add"
        
        # Prepare the payload according to 3X-UI core specifications
        client_payload = {
            "client": {
                "email": email,
                "totalGB": total_bytes,  # Total data limit specified in bytes
                "expiryTime": 0,         # 0 means unlimited duration on panel side
                "tgId": 0,
                "limitIp": 0,
                "enable": True
            },
            "inboundIds": [inbound_id]
        }
        
        custom_headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Telegram-Sanayi-Bot"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(add_url, json=client_payload, headers=custom_headers, timeout=12.0)
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Panel returned non-200 status: {response.status_code} - {response.text}")
                    return {"success": False, "msg": f"Status code: {response.status_code}"}
            except httpx.RequestError as exc:
                logger.error(f"Network exception connection to panel: {exc}")
                return {"success": False, "msg": "Panel connection timeout or network error"}