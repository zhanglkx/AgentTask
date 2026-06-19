"""第 1 章 conftest：将 src/ 加入 sys.path。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
