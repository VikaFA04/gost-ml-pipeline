"""
Phase 8 milestone-smoke: Streamlit headless boot gate.

D-C-04: boots app.py headless on port 8502, confirms HTTP 200 within 30s,
then shuts down cleanly. Catches import-time errors that pytest.importorskip misses.

Also asserts app.SUPPORTED_UPLOAD_TYPES == ["docx", "pdf"] (Phase 7 D-04 §3).

Gated by pytest.importorskip("streamlit") + pytest.importorskip("requests").
Port 8502 chosen to avoid conflict with developer-running instance on 8501.
"""
from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

_REPO = Path(__file__).parent.parent
_PORT = 8502


def _port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


@pytest.fixture(scope="module")
def streamlit_process():
    pytest.importorskip("requests")
    pytest.importorskip("streamlit")

    if not _port_free(_PORT):
        pytest.skip(f"Port {_PORT} already in use — cannot launch headless Streamlit")

    proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run",
            str(_REPO / "app.py"),
            "--server.headless", "true",
            "--server.port", str(_PORT),
            "--server.runOnSave", "false",
            "--logger.level", "error",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(_REPO),
    )

    import requests

    deadline = time.monotonic() + 30
    started = False
    while time.monotonic() < deadline:
        try:
            r = requests.get(f"http://127.0.0.1:{_PORT}", timeout=2)
            if r.status_code == 200:
                started = True
                break
        except Exception:
            time.sleep(0.5)

    if not started:
        proc.terminate()
        proc.wait(timeout=5)
        pytest.fail("Streamlit did not start within 30s on port 8502")

    yield proc

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def test_streamlit_boots_to_200(streamlit_process) -> None:
    """D-C-04: Streamlit app.py must respond HTTP 200 within 30s."""
    import requests
    r = requests.get(f"http://127.0.0.1:{_PORT}", timeout=5)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"


def test_streamlit_app_upload_contract() -> None:
    """D-C-04: app.SUPPORTED_UPLOAD_TYPES must equal ['docx', 'pdf'] (Phase 7 D-04 §3)."""
    pytest.importorskip("streamlit")
    import importlib
    if "app" in sys.modules:
        del sys.modules["app"]
    import importlib.util
    spec = importlib.util.spec_from_file_location("app", _REPO / "app.py")
    app_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_mod)
    assert app_mod.SUPPORTED_UPLOAD_TYPES == ["docx", "pdf"], (
        f"app.SUPPORTED_UPLOAD_TYPES={app_mod.SUPPORTED_UPLOAD_TYPES!r}; "
        "expected ['docx', 'pdf'] per Phase 7 D-04 §3"
    )
