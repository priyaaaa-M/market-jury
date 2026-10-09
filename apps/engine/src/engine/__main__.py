import os

import uvicorn

from .api import create_app
from .orchestrator import Engine
from .store import Store

if __name__ == "__main__":
    engine = Engine(store=Store(os.getenv("DB_PATH", "engine.db")))
    uvicorn.run(create_app(engine), host=os.getenv("HOST", "127.0.0.1"),
                port=int(os.getenv("PORT", "8008")))
