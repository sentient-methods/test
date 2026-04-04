"""GitHub sync — pushes generated projects to GitHub repos.

When an agent builds something, this module creates a GitHub repo
and pushes the workspace contents to it. The CEO gets a repo URL
they can share, clone, or deploy from.

No volumes needed. GitHub IS the persistence layer.
"""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


def _slugify(text: str) -> str:
    """Turn a CEO directive into a valid repo name."""
    slug = re.sub(r"[^a-zA-Z0-9\s-]", "", text.lower())
    slug = re.sub(r"[\s]+", "-", slug.strip())
    slug = slug[:50].rstrip("-")
    return slug or "project"


async def create_repo(name: str, description: str = "") -> dict | None:
    """Create a new GitHub repo under the configured owner."""
    if not settings.github_token or not settings.github_owner:
        logger.warning("GitHub not configured — skipping repo creation")
        return None

    headers = {
        "Authorization": f"token {settings.github_token}",
        "Accept": "application/vnd.github+json",
    }

    # Check if creating under a user or an org
    async with httpx.AsyncClient() as client:
        # Try org first
        resp = await client.post(
            f"{GITHUB_API}/orgs/{settings.github_owner}/repos",
            headers=headers,
            json={
                "name": name,
                "description": description,
                "private": False,
                "auto_init": False,
            },
        )

        if resp.status_code == 404:
            # Not an org — try as user
            resp = await client.post(
                f"{GITHUB_API}/user/repos",
                headers=headers,
                json={
                    "name": name,
                    "description": description,
                    "private": False,
                    "auto_init": False,
                },
            )

        if resp.status_code in (201, 200):
            data = resp.json()
            logger.info("Created GitHub repo: %s", data.get("html_url"))
            return data
        else:
            logger.error("Failed to create repo: %s %s", resp.status_code, resp.text)
            return None


async def push_workspace_to_github(
    workspace_path: str,
    repo_name: str,
    description: str = "",
    commit_message: str = "Initial build by MakeItHappen",
) -> str | None:
    """Push a workspace directory to a new GitHub repo.

    Returns the repo URL on success, None on failure.
    """
    if not settings.github_token or not settings.github_owner:
        logger.warning("GitHub not configured (set GITHUB_TOKEN and GITHUB_OWNER)")
        return None

    workspace = Path(workspace_path)
    if not workspace.exists():
        logger.error("Workspace does not exist: %s", workspace_path)
        return None

    # Check if there are any files to push
    files = [f for f in workspace.rglob("*") if f.is_file() and ".git" not in f.parts]
    if not files:
        logger.warning("Workspace is empty, nothing to push")
        return None

    # Create the repo
    repo_data = await create_repo(repo_name, description)
    if not repo_data:
        return None

    clone_url = repo_data.get("clone_url", "")
    html_url = repo_data.get("html_url", "")

    # Inject token into clone URL for auth
    auth_url = clone_url.replace("https://", f"https://x-access-token:{settings.github_token}@")

    try:
        cwd = str(workspace)

        # Ensure git is initialized
        _run_git(["git", "init"], cwd)
        _run_git(["git", "config", "user.email", "makeitahppen@ceo.ai"], cwd)
        _run_git(["git", "config", "user.name", "MakeItHappen"], cwd)

        # Add all files
        _run_git(["git", "add", "-A"], cwd)

        # Commit
        _run_git(["git", "commit", "-m", commit_message], cwd)

        # Set remote and push
        _run_git(["git", "remote", "remove", "origin"], cwd, ignore_errors=True)
        _run_git(["git", "remote", "add", "origin", auth_url], cwd)
        _run_git(["git", "branch", "-M", "main"], cwd)
        _run_git(["git", "push", "-u", "origin", "main"], cwd)

        logger.info("Pushed workspace to %s", html_url)
        return html_url

    except Exception as e:
        logger.exception("Failed to push to GitHub: %s", e)
        return None


async def sync_workspace(
    session_id: str,
    workspace_path: str,
    intent_summary: str,
) -> str | None:
    """High-level: create a repo from a session's workspace and push it.

    Called by the orchestrator after agents complete their work.
    Returns the GitHub repo URL.
    """
    repo_name = _slugify(intent_summary)

    # Avoid collisions by appending session ID
    repo_name = f"{repo_name}-{session_id[:6]}"

    return await push_workspace_to_github(
        workspace_path=workspace_path,
        repo_name=repo_name,
        description=f"Built by MakeItHappen: {intent_summary}",
        commit_message=f"Build: {intent_summary}\n\nGenerated by MakeItHappen",
    )


def _run_git(cmd: list[str], cwd: str, ignore_errors: bool = False) -> str:
    """Run a git command in a directory."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0 and not ignore_errors:
        logger.warning("Git command failed: %s\nstderr: %s", " ".join(cmd), result.stderr)
    return result.stdout
