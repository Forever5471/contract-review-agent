from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
DEPS = ROOT / ".tmp-python-deps"
if DEPS.exists():
    sys.path.insert(0, str(DEPS))

import uvicorn


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8123)
