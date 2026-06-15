# Project Structure Overview

## Architecture

```
telegrom-bot/
├── main.py                 # FastAPI application entry point
├── bot.py                  # Telegram bot setup and lifecycle
├── config.py               # Settings and environment config
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
│
├── services/               # Business logic layer
│   ├── __init__.py
│   └── panel.py            # 3X-UI Panel API client
│
└── handlers/               # Telegram command handlers
    ├── __init__.py
    └── commands.py         # Command implementations
```

## Components

### main.py

- FastAPI application with lifespan management
- REST endpoints for panel operations
- Bot lifecycle integration

### bot.py

- Telegram bot initialization
- Command handler registration
- Polling management

### config.py

- Centralized settings from .env
- Configuration constants

### services/panel.py

- PanelAPIClient class
- Async HTTP operations
- Error handling

### handlers/commands.py

- /start command
- /clients command (list all clients)
- /test command (create test client)

## Running the Application

```bash
pip install -r requirements.txt
python main.py
```

The bot will:

1. Connect to 3X-UI Panel API
2. Start polling for Telegram messages
3. Expose REST endpoints at http://localhost:8000
