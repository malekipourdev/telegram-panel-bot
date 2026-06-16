import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PANEL_BASE_URL: str = os.getenv("SANAYI_API_BASE_URL", "https://start724.online:48127")
    PANEL_API_TOKEN: str = os.getenv("SANAYI_API_SECRET", "BcHHuqGxpAbcf6b1vBZf96px3lZ3pKBKC62bCCFq1Eij2Ivj")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "test_token_12345")
    
    PANEL_WEB_PATH: str = "Nao4H5JUx1fD5hQY60"
    DEFAULT_INBOUND_ID: int = 1
    TEST_CLIENT_SIZE_BYTES: int = 52428800
    
    API_TIMEOUT: float = 12.0
    LOG_LEVEL: str = "INFO"
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://panel_user:panel_pass_123@localhost:3306/telegram_panel"
    )
    
    REFERRAL_REWARD_AMOUNT: float = 10000.0
    REFERRAL_PERCENTAGE: float = 0.1


settings = Settings()
