"""Make the repo importable when running ``pytest`` from a checkout without an
editable install (CI uses ``maturin develop``; local dev may not)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
