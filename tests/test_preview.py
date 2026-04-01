"""Tests for the preview system."""

import os
import tempfile
from pathlib import Path
from backend.tools.preview import _detect_project_and_command, PreviewManager


class TestProjectDetection:
    def test_detect_node_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "package.json").write_text('{"scripts": {"dev": "vite"}}')
            project_type, cmd = _detect_project_and_command(Path(tmpdir), 3000)
            assert project_type == "node"
            assert cmd is not None

    def test_detect_static_html(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "index.html").write_text("<html></html>")
            project_type, cmd = _detect_project_and_command(Path(tmpdir), 3000)
            assert project_type == "static"

    def test_detect_django(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "manage.py").write_text("")
            project_type, cmd = _detect_project_and_command(Path(tmpdir), 3000)
            assert project_type == "django"

    def test_detect_python_app(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "app.py").write_text("")
            project_type, cmd = _detect_project_and_command(Path(tmpdir), 3000)
            assert project_type == "python"

    def test_detect_unknown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_type, cmd = _detect_project_and_command(Path(tmpdir), 3000)
            assert project_type == "unknown"
            assert cmd is None


class TestPreviewManager:
    def test_next_port(self):
        manager = PreviewManager()
        assert manager._next_port() == 3100

    def test_get_nonexistent(self):
        manager = PreviewManager()
        assert manager.get_preview("/nonexistent") is None
