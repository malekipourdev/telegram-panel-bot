import logging
from fastapi import FastAPI, HTTPException, status
from contextlib import asynccontextmanager

from config import settings
from services.panel import PanelAPIClient

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

panel_client = PanelAPIClient()
bot_instance = None


async def lifespan(app: FastAPI):
    from bot import setup_bot, stop_bot
    
    global bot_instance
    try:
        logger.info("Starting bot...")
        bot_instance = await setup_bot()
        yield
    finally:
        if bot_instance:
            await stop_bot(bot_instance)


app = FastAPI(title="3X-UI Panel Bot API", lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/clients")
async def get_clients():
    try:
        data = await panel_client.get_clients_list()
        return data
    except Exception as e:
        logger.error(f"Error fetching clients: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to fetch clients from panel"
        )


@app.post("/api/clients/test")
async def create_test_client():
    import uuid
    
    try:
        test_email = f"test_{uuid.uuid4().hex[:8]}"
        result = await panel_client.create_client(
            email=test_email,
            total_bytes=settings.TEST_CLIENT_SIZE_BYTES,
            inbound_id=settings.DEFAULT_INBOUND_ID
        )
        
        if result.get("success"):
            return {"email": test_email, "success": True}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("msg", "Failed to create client")
            )
    except Exception as e:
        logger.error(f"Error creating test client: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to create test client"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)