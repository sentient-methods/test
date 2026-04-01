"""Preview system — launches dev servers and captures output for the CEO.

Handles:
- Web projects (npm/vite/next dev servers)
- Python projects (Flask/FastAPI/Django)
- Static HTML files
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PreviewServer:
    """A running preview server."""
    port: int
    process: asyncio.subprocess.Process | None = None
    url: str = ""
    project_type: str = "unknown"

    async def stop(self) -> None:
        if self.process and self.process.returncode is None:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except (asyncio.TimeoutError, ProcessLookupError):
                self.process.kill()


@dataclass
class PreviewManager:
    """Manages preview servers for generated projects."""
    _servers: dict[str, PreviewServer] = field(default_factory=dict)
    _base_port: int = 3100

    def _next_port(self) -> int:
        used = {s.port for s in self._servers.values()}
        port = self._base_port
        while port in used:
            port += 1
        return port

    async def start_preview(self, project_dir: str) -> PreviewServer:
        """Detect project type and start appropriate dev server."""
        project_path = Path(project_dir)

        # Stop existing preview for this project
        if project_dir in self._servers:
            await self._servers[project_dir].stop()

        port = self._next_port()
        project_type, cmd = _detect_project_and_command(project_path, port)

        if not cmd:
            return PreviewServer(port=port, project_type="static", url=f"file://{project_path}/index.html")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(project_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "PORT": str(port)},
        )

        server = PreviewServer(
            port=port,
            process=process,
            url=f"http://localhost:{port}",
            project_type=project_type,
        )
        self._servers[project_dir] = server

        # Give the server a moment to start
        await asyncio.sleep(2)

        logger.info("Preview server started: %s on port %d", project_type, port)
        return server

    async def stop_preview(self, project_dir: str) -> None:
        if project_dir in self._servers:
            await self._servers[project_dir].stop()
            del self._servers[project_dir]

    async def stop_all(self) -> None:
        for server in self._servers.values():
            await server.stop()
        self._servers.clear()

    def get_preview(self, project_dir: str) -> PreviewServer | None:
        return self._servers.get(project_dir)


def _detect_project_and_command(project_path: Path, port: int) -> tuple[str, list[str] | None]:
    """Detect project type and return the appropriate dev server command."""
    # Check for Node.js projects
    package_json = project_path / "package.json"
    if package_json.exists():
        # Check for common frameworks
        try:
            import json
            pkg = json.loads(package_json.read_text())
            scripts = pkg.get("scripts", {})

            if "dev" in scripts:
                return ("node", ["npx", "--yes", "npm", "run", "dev", "--", "--port", str(port)])
            if "start" in scripts:
                return ("node", ["npx", "--yes", "npm", "run", "start"])
        except Exception:
            pass
        return ("node", ["npx", "--yes", "npm", "run", "dev"])

    # Check for Python web projects
    if (project_path / "manage.py").exists():
        return ("django", ["python", "manage.py", "runserver", f"0.0.0.0:{port}"])
    if (project_path / "app.py").exists() or (project_path / "main.py").exists():
        entry = "app.py" if (project_path / "app.py").exists() else "main.py"
        return ("python", ["python", "-m", "uvicorn", f"{entry.replace('.py', '')}:app", "--port", str(port)])

    # Check for static HTML
    if (project_path / "index.html").exists():
        return ("static", ["python", "-m", "http.server", str(port)])

    return ("unknown", None)


# Global preview manager
preview_manager = PreviewManager()
