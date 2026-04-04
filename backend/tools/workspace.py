"""Workspace manager — creates and manages isolated project directories.

Each CEO session gets its own workspace directory where agents can
read, write, edit files, and run commands. This is the "office" where
the engineering team does its work.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

WORKSPACES_ROOT = Path(os.environ.get("WORKSPACES_ROOT", "/workspaces"))


def ensure_workspace(session_id: str) -> Path:
    """Create and return the workspace directory for a session.

    Initializes a git repo in the workspace so agents can track changes
    and the CEO can see diffs / rollback.
    """
    workspace = WORKSPACES_ROOT / session_id
    workspace.mkdir(parents=True, exist_ok=True)

    # Initialize git if not already done
    git_dir = workspace / ".git"
    if not git_dir.exists():
        subprocess.run(
            ["git", "init"],
            cwd=str(workspace),
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "makeitahppen@ceo.ai"],
            cwd=str(workspace),
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "MakeItHappen"],
            cwd=str(workspace),
            capture_output=True,
        )

    return workspace


def list_workspaces() -> list[dict]:
    """List all existing workspaces with basic info."""
    if not WORKSPACES_ROOT.exists():
        return []

    workspaces = []
    for path in WORKSPACES_ROOT.iterdir():
        if path.is_dir() and not path.name.startswith("."):
            files = list(path.rglob("*"))
            files = [f for f in files if f.is_file() and ".git" not in f.parts]
            workspaces.append({
                "session_id": path.name,
                "path": str(path),
                "file_count": len(files),
            })
    return workspaces


def get_workspace_files(session_id: str) -> list[str]:
    """List all files in a workspace (excluding .git)."""
    workspace = WORKSPACES_ROOT / session_id
    if not workspace.exists():
        return []

    files = []
    for path in workspace.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            files.append(str(path.relative_to(workspace)))
    return sorted(files)


def delete_workspace(session_id: str) -> bool:
    """Delete a workspace and all its contents."""
    import shutil
    workspace = WORKSPACES_ROOT / session_id
    if workspace.exists():
        shutil.rmtree(workspace)
        return True
    return False


def get_workspace_tree(session_id: str) -> str:
    """Get a tree view of the workspace for agent context."""
    files = get_workspace_files(session_id)
    if not files:
        return "Empty workspace — nothing built yet."

    lines = [f"Workspace: /workspaces/{session_id}", f"Files ({len(files)}):"]
    for f in files[:50]:  # Cap at 50 for context window
        lines.append(f"  {f}")
    if len(files) > 50:
        lines.append(f"  ... and {len(files) - 50} more")
    return "\n".join(lines)
