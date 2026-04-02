import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.chat.router import router as chat_router
from backend.chat.session import store
from backend.tools.preview import preview_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    await store.load_all()
    logging.getLogger(__name__).info("MakeItHappen is ready. As you wish, CEO.")
    yield
    await preview_manager.stop_all()


app = FastAPI(
    title="MakeItHappen",
    description="The CEO's engineering org in a box. As you wish.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")


@app.get("/health")
async def health():
    return {
        "status": "ready",
        "motto": "Just do it.",
        "slogan": "Make it happen.",
        "tagline": "As you wish.",
    }


@app.get("/api/preview/{session_id}")
async def get_preview(session_id: str):
    """Get the preview URL for a session's project."""
    session = store.get(session_id)
    if not session:
        return {"error": "Session not found"}

    server = preview_manager.get_preview(session.project_dir)
    if server:
        return {"url": server.url, "project_type": server.project_type, "port": server.port}

    server = await preview_manager.start_preview(session.project_dir)
    return {"url": server.url, "project_type": server.project_type, "port": server.port}


# Serve built frontend in production
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve the React SPA — all non-API routes return index.html."""
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")


def run():
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    run()
