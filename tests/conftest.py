from __future__ import annotations

import os
from pathlib import Path


TEST_RUNTIME_ROOT = Path(".pytest_runtime")
os.environ["DATA_DIR"] = str(TEST_RUNTIME_ROOT / "data")
os.environ["OUTPUTS_DIR"] = str(TEST_RUNTIME_ROOT / "outputs")
os.environ["WORKSPACES_DIR"] = str(TEST_RUNTIME_ROOT / "workspaces")
