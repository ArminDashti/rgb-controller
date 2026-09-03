from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes

from app import modes, store

_stop = threading.Event()
_thread: threading.Thread | None = None
_idle_applied = False


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


def _idle_seconds() -> float:
    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
        return 0.0
    tick = ctypes.windll.kernel32.GetTickCount()
    return max(0.0, (tick - info.dwTime) / 1000.0)


def _restore_if_needed() -> None:
    global _idle_applied
    if not _idle_applied:
        return
    previous = modes.last_user_mode()
    if previous:
        try:
            modes.apply_mode(previous, remember=False)
        except Exception:
            pass
    _idle_applied = False


def _loop() -> None:
    global _idle_applied
    while not _stop.wait(2.0):
        settings = store.get_settings()
        mode_id = (settings.get("idle_mode_id") or "").strip()
        minutes = int(settings.get("idle_minutes") or 0)
        if not mode_id or minutes < 1:
            _restore_if_needed()
            continue
        idle = _idle_seconds()
        if idle >= minutes * 60:
            if not _idle_applied:
                try:
                    modes.apply_mode({"mode_id": mode_id}, remember=False)
                    _idle_applied = True
                except Exception:
                    pass
        else:
            _restore_if_needed()


def start() -> None:
    global _thread
    if _thread and _thread.is_alive():
        return
    _stop.clear()
    _thread = threading.Thread(target=_loop, name="rgb-idle", daemon=True)
    _thread.start()


def stop() -> None:
    _stop.set()
