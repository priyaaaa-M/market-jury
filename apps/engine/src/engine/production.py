"""Single-origin production entrypoint: authenticated /api and compiled SPA."""
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import create_app
from .orchestrator import Engine
from .store import Store


def production_app() -> FastAPI:
    key = os.getenv("API_KEY")
    if not key or len(key) < 24:
        raise RuntimeError("Set a strong API_KEY (24+ characters) in server environment")
    root = Path(os.getenv("WEB_DIST", "/app/web-dist")).resolve()
    if not (root / "index.html").is_file():
        raise RuntimeError("Compiled frontend missing")
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    engine = Engine(store=Store(os.getenv("DB_PATH", "/tmp/market-jury.db")))
    app.mount("/api", create_app(engine, api_key=key))
    app.mount("/assets", StaticFiles(directory=root / "assets"), name="assets")
    @app.get("/health")
    def health(): return {"ok":True}
    @app.get("/{path:path}")
    def spa(path: str):
        if path.startswith("api/"): raise HTTPException(404)
        return FileResponse(root / "index.html", headers={"Cache-Control":"no-cache"})
    return app

def main():
    uvicorn.run(production_app(),host="0.0.0.0",port=int(os.getenv("PORT","10000")))

if __name__ == "__main__": main()
