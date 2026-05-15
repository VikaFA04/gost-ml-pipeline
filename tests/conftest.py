# Shared pytest configuration for Phase 6 Streamlit UI tests.
#
# Adds the repo root to sys.path so `import app` and `from src.inference.run_log import RunLog`
# resolve when pytest is invoked from outside the repo root. This is the standard pytest
# convention used implicitly via `python -m pytest` (per RESEARCH §10 OQ-3).
#
# Provides a single `app_test` fixture that constructs `streamlit.testing.v1.AppTest`
# pointing at the project's `app.py`. The fixture body uses `pytest.importorskip("streamlit")`
# so any test that consumes the fixture is skipped cleanly when run on a Python interpreter
# without Streamlit installed (system Python). File collection itself never imports
# Streamlit, so non-Streamlit tests in the suite are unaffected.

from __future__ import annotations

import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def app_test():
    """AppTest instance pointing at the project's app.py.

    Skips the test if Streamlit is not importable in the current interpreter
    (e.g. running pytest from system Python without the project venv).
    """
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    return AppTest.from_file(str(REPO_ROOT / "app.py"))
