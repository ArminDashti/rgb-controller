from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from app.config import PORT, ROOT

TASK_NAME = "RGBControllerApi"


def _python() -> str:
    return sys.executable


def _tr_command(openrgb_exe: str) -> str:
    api = f'"{_python()}" -m uvicorn app.main:app --host 127.0.0.1 --port {PORT}'
    if openrgb_exe and Path(openrgb_exe).exists():
        return f'cmd /c start "" "{openrgb_exe}" --server --server-port 6742 & cd /d "{ROOT}" & {api}'
    return f'cmd /c cd /d "{ROOT}" & {api}'


def set_run_startup(enabled: bool, openrgb_exe: str = "") -> None:
    if os.name != "nt":
        return
    schtasks = shutil.which("schtasks") or "schtasks"
    subprocess.run([schtasks, "/Delete", "/TN", TASK_NAME, "/F"], capture_output=True, check=False)
    if not enabled:
        return
    tr = _tr_command(openrgb_exe)
    subprocess.run(
        [
            schtasks,
            "/Create",
            "/TN",
            TASK_NAME,
            "/SC",
            "ONLOGON",
            "/RL",
            "LIMITED",
            "/F",
            "/TR",
            tr,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
