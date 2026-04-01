import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    # Load persisted sessions
    await store.load_all()
    logging.getLogger(__name__).info("MakeItHappen is ready. As you wish, CEO.")
    yield
    # Cleanup preview servers
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

    # Try to start a preview
    server = await preview_manager.start_preview(session.project_dir)
    return {"url": server.url, "project_type": server.project_type, "port": server.port}


def run():
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
