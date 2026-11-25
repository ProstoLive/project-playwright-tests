"""Корневой conftest: путь импорта и подключение фикстур."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

pytest_plugins = ["core.runner.conftest"]
