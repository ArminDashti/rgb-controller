from __future__ import annotations

import threading
from typing import Any

from openrgb import OpenRGBClient
from openrgb.utils import RGBColor

from app.config import CLIENT_NAME
from app import store

_lock = threading.RLock()
_client: OpenRGBClient | None = None
_last_error: str = ""
_connected_host: str = ""
_connected_port: int = 0


def _scale(color: RGBColor, brightness: float) -> RGBColor:
    factor = max(0.0, min(1.0, brightness))
    return RGBColor(
        int(color.red * factor),
        int(color.green * factor),
        int(color.blue * factor),
    )


def rgb_from_hex(value: str, brightness: float = 1.0) -> RGBColor:
    raw = (value or "#00a3e0").lstrip("#")
    if len(raw) != 6:
        raw = "00a3e0"
    color = RGBColor(int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16))
    return _scale(color, brightness)


def effective_brightness(mode_brightness: int | None = None) -> float:
    settings = store.get_settings()
    backlight = max(0, min(100, int(settings["backlight_percent"]))) / 100.0
    extra = 1.0 if mode_brightness is None else max(0, min(100, int(mode_brightness))) / 100.0
    return backlight * extra


def status() -> dict[str, Any]:
    settings = store.get_settings()
    with _lock:
        return {
            "connected": _client is not None,
            "last_error": _last_error,
            "host": settings["openrgb_host"],
            "port": settings["openrgb_port"],
            "connected_host": _connected_host,
            "connected_port": _connected_port,
        }


def disconnect() -> None:
    global _client, _connected_host, _connected_port
    with _lock:
        if _client is not None:
            try:
                _client.disconnect()
            except Exception:
                pass
            _client = None
            _connected_host = ""
            _connected_port = 0


def connect(host: str | None = None, port: int | None = None) -> OpenRGBClient:
    global _client, _last_error, _connected_host, _connected_port
    settings = store.get_settings()
    address = host or settings["openrgb_host"]
    sdk_port = int(port or settings["openrgb_port"])
    with _lock:
        disconnect()
        try:
            client = OpenRGBClient(address=address, port=sdk_port, name=CLIENT_NAME)
            _client = client
            _last_error = ""
            _connected_host = address
            _connected_port = sdk_port
            return client
        except Exception as exc:
            _client = None
            _last_error = str(exc)
            raise


def ensure_client() -> OpenRGBClient:
    settings = store.get_settings()
    with _lock:
        if (
            _client is not None
            and _connected_host == settings["openrgb_host"]
            and _connected_port == int(settings["openrgb_port"])
        ):
            try:
                _client.update()
                return _client
            except Exception:
                disconnect()
    return connect()


def test_connect(host: str, port: int) -> dict[str, Any]:
    try:
        client = OpenRGBClient(address=host, port=int(port), name=f"{CLIENT_NAME}-test")
        count = len(client.devices)
        try:
            client.disconnect()
        except Exception:
            pass
        return {"ok": True, "device_count": count, "error": ""}
    except Exception as exc:
        return {"ok": False, "device_count": 0, "error": str(exc)}


def serialize_color(color: Any) -> dict[str, int]:
    return {"r": int(getattr(color, "red", 0)), "g": int(getattr(color, "green", 0)), "b": int(getattr(color, "blue", 0))}


def serialize_device(device: Any, detail: bool = False) -> dict[str, Any]:
    active_name = ""
    try:
        active_name = device.modes[device.active_mode].name
    except Exception:
        active_name = ""
    colors = []
    try:
        colors = [serialize_color(c) for c in (device.colors or [])[:8]]
    except Exception:
        colors = []
    payload: dict[str, Any] = {
        "id": int(device.id),
        "name": device.name,
        "type": getattr(device.type, "name", str(device.type)),
        "led_count": len(device.leds or []),
        "active_mode": active_name,
        "colors": colors,
    }
    if detail:
        payload["modes"] = [
            {
                "id": idx,
                "name": mode.name,
                "speed": getattr(mode, "speed", None),
            }
            for idx, mode in enumerate(device.modes or [])
        ]
        payload["zones"] = []
        for zone in device.zones or []:
            matrix = None
            if getattr(zone, "mat_width", None) and getattr(zone, "mat_height", None):
                matrix = {
                    "width": zone.mat_width,
                    "height": zone.mat_height,
                    "map": zone.matrix_map,
                }
            payload["zones"].append(
                {
                    "id": zone.id,
                    "name": zone.name,
                    "led_count": len(zone.leds or []),
                    "matrix": matrix,
                }
            )
    return payload


def list_devices() -> list[dict[str, Any]]:
    client = ensure_client()
    with _lock:
        return [serialize_device(device) for device in client.devices]


def get_device(device_id: int) -> dict[str, Any]:
    client = ensure_client()
    with _lock:
        for device in client.devices:
            if int(device.id) == int(device_id):
                return serialize_device(device, detail=True)
    raise KeyError(f"device {device_id} not found")


def iter_devices(device_ids: list[int] | None):
    client = ensure_client()
    with _lock:
        devices = list(client.devices)
    if not device_ids:
        return devices
    wanted = set(int(i) for i in device_ids)
    return [d for d in devices if int(d.id) in wanted]


def try_set_mode(device: Any, names: list[str], speed: int | None = None) -> bool:
    lowered = [n.lower() for n in names]
    for mode in device.modes or []:
        if mode.name.lower() in lowered:
            if speed is not None and hasattr(mode, "speed") and getattr(mode, "speed_min", None) is not None:
                lo = int(mode.speed_min)
                hi = int(mode.speed_max)
                mode.speed = lo + int((hi - lo) * max(0, min(100, speed)) / 100)
            device.set_mode(mode)
            return True
    return False


def set_direct_color(device: Any, color: RGBColor) -> None:
    try:
        device.set_custom_mode()
    except Exception:
        try:
            device.set_mode("direct")
        except Exception:
            pass
    device.set_color(color, fast=True)


def set_led_colors(device: Any, colors: list[RGBColor]) -> None:
    try:
        device.set_custom_mode()
    except Exception:
        pass
    if len(colors) != len(device.leds):
        if not device.leds:
            return
        padded = (colors * ((len(device.leds) // max(1, len(colors))) + 1))[: len(device.leds)]
        device.set_colors(padded, fast=True)
        return
    device.set_colors(colors, fast=True)


def set_device_mode(device_id: int, name: str) -> None:
    devices = iter_devices([device_id])
    if not devices:
        raise KeyError(f"device {device_id} not found")
    with _lock:
        devices[0].set_mode(name)
    client = ensure_client()
    with _lock:
        try:
            client.clear()
        except Exception:
            for device in client.devices:
                set_direct_color(device, RGBColor(0, 0, 0))
