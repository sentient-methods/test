"""Project state tracker — the institutional memory of what's been built.

Maintains awareness of the project structure so agents have context
about what exists before they start creating or modifying things.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProjectState:
    """Snapshot of the current project structure and stack."""
    root: str = "."
    files: list[str] = field(default_factory=list)
    detected_stack: dict[str, str] = field(default_factory=dict)

    def scan(self) -> None:
        """Scan the project directory and detect the stack."""
        self.files = []
        root = Path(self.root)

        for path in root.rglob("*"):
            if path.is_file() and ".git" not in path.parts and "node_modules" not in path.parts:
                self.files.append(str(path.relative_to(root)))

        self._detect_stack()

    def _detect_stack(self) -> None:
        """Detect the technology stack from project files."""
        markers = {
            "package.json": ("runtime", "Node.js"),
            "pyproject.toml": ("runtime", "Python"),
            "Cargo.toml": ("runtime", "Rust"),
            "go.mod": ("runtime", "Go"),
            "tsconfig.json": ("language", "TypeScript"),
            "next.config.js": ("framework", "Next.js"),
            "next.config.mjs": ("framework", "Next.js"),
            "vite.config.ts": ("bundler", "Vite"),
            "tailwind.config.js": ("styling", "Tailwind CSS"),
            "tailwind.config.ts": ("styling", "Tailwind CSS"),
            "Dockerfile": ("infra", "Docker"),
            ".github/workflows": ("ci", "GitHub Actions"),
        }

        for filename, (category, tech) in markers.items():
            if filename in self.files:
                self.detected_stack[category] = tech

    def summary(self) -> str:
        """Human-readable project summary for agent context."""
        if not self.files:
            return "Empty project — nothing built yet."

        lines = [f"Project root: {self.root}", f"Files: {len(self.files)}"]

        if self.detected_stack:
            stack = ", ".join(f"{v} ({k})" for k, v in self.detected_stack.items())
            lines.append(f"Stack: {stack}")

        # Show top-level structure
        top_level = sorted(set(f.split(os.sep)[0] for f in self.files))
        lines.append(f"Top-level: {', '.join(top_level[:15])}")

        return "\n".join(lines)
