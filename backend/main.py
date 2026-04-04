import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.chat.router import router as chat_router
from backend.chat.session import store
from backend.tools.preview import preview_manager
from backend.tools.workspace import list_workspaces, delete_workspace, get_workspace_files
from backend.tools.cost_tracker import cost_tracker

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


# --- Health ---

@app.get("/health")
async def health():
    return {
        "status": "ready",
        "motto": "Just do it.",
        "slogan": "Make it happen.",
        "tagline": "As you wish.",
    }


# --- Cost Tracking ---

@app.get("/api/costs")
async def get_total_costs():
    """Get total spend across all sessions."""
    return cost_tracker.get_total_spend()


@app.get("/api/costs/{session_id}")
async def get_session_costs(session_id: str):
    """Get cost breakdown for a specific session."""
    summary = cost_tracker.get_summary(session_id)
    session_cost = cost_tracker.get_or_create(session_id)
    summary["run_cost_estimate"] = session_cost.estimate_monthly_run_cost()
    return summary


# --- Workspaces ---

@app.get("/api/workspaces")
async def get_workspaces():
    """List all project workspaces."""
    return list_workspaces()


@app.get("/api/workspaces/{session_id}/files")
async def get_files(session_id: str):
    """List all files in a session's workspace."""
    files = get_workspace_files(session_id)
    return {"session_id": session_id, "files": files, "file_count": len(files)}


# --- Clean Removal ---

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Cleanly remove a session, its workspace, and all generated files.

    This is the CEO saying 'kill that project.'
    """
    # Stop any preview server
    session = store.get(session_id)
    if session:
        await preview_manager.stop_preview(session.project_dir)

    # Delete workspace files
    workspace_deleted = delete_workspace(session_id)

    # Remove from session store
    removed = store.remove(session_id)

    return {
        "session_id": session_id,
        "session_removed": removed,
        "workspace_deleted": workspace_deleted,
        "status": "Removed. As you wish, CEO.",
    }


# --- Preview ---

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


# --- Dashboard ---

@app.get("/api/dashboard")
async def dashboard():
    """CEO dashboard — everything at a glance."""
    sessions = store.list_all()
    workspaces = list_workspaces()
    costs = cost_tracker.get_total_spend()

    return {
        "sessions": [
            {
                "id": s.id,
                "created_at": s.created_at.isoformat(),
                "message_count": len(s.messages),
                "last_intent": s.context.get("last_intent", ""),
                "cost": cost_tracker.get_summary(s.id),
            }
            for s in sessions
        ],
        "workspaces": workspaces,
        "total_spend": costs["total_cost_usd"],
        "session_count": len(sessions),
    }


# --- Serve built frontend in production ---

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
