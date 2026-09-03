from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _env(key: str, default: str) -> str:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        return default
    return value.strip()


ADDR = _env("ADDR", "0.0.0.0")
PORT = int(_env("PORT", "8132"))
SQLITE_PATH = Path(_env("SQLITE_PATH", str(ROOT / "data" / "rgb-controller.db")))
WEBUI_ORIGIN = _env("WEBUI_ORIGIN", "http://localhost:5182")
CLIENT_NAME = "rgb-controller-api"
