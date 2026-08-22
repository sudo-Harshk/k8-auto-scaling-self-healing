"""conftest.py for pytest — adds /code to sys.path so `from src.X import Z` works.

This is the same path convention as the rest of the project: the Docker
image's WORKDIR is /code but `src` is not on sys.path automatically for
the `from src...` import style.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))