import httpx
from fastapi import FastAPI, HTTPException, status

app = FastAPI(title="3X-UI Panel Bridge API")

# Setup configuration according to your Swagger screenshot
# Do not include the trailing slash at the end of the base URL
PANEL_BASE_URL = "https://start724.online:48127"
PANEL_WEB_BASE_PATH = "Nao4H5JUx1fD5hQY60"  # Your unique panel URL path

# Replace this with your actual API Token from Settings -> Security
API_BEARER_TOKEN = "BcHHuqGxpAbcf6b1vBZf96px3lZ3pKBKC62bCCFq1Eij2Ivj"

@app.get("/clients", tags=["Testing"])
async def get_panel_clients():
    """
    Fetches the clients list from 3X-UI panel using Bearer Token Authentication.
    """
    # Constructing the exact URL from your screenshot:
    list_url = f"{PANEL_BASE_URL}/{PANEL_WEB_BASE_PATH}/panel/api/clients/list"
    
    # Setting up the Bearer Token authentication headers as requested by 3X-UI docs
    custom_headers = {
        "Authorization": f"Bearer {API_BEARER_TOKEN}",
        "Accept": "application/json",
        "User-Agent": "FastAPI-Bot-Bridge"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Sending the asynchronous GET request with Bearer token headers
            response = await client.get(list_url, headers=custom_headers, timeout=12.0)
            
            # Handle standard authentication or route errors
            if response.status_code == 401 or response.status_code == 403:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired API Bearer Token. Please check panel settings."
                )
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_BAD_GATEWAY,
                    detail=f"Panel API responded with status code: {response.status_code}"
                )
                
            # Returns the successful JSON client list to your frontend/client
            return response.json()

        except httpx.RequestError as exc:
            # Captures network layer issues (DNS failure, connection timeouts, etc.)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Network error trying to reach the upstream panel server: {exc}"
            )