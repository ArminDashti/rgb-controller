from __future__ import annotations

import math
import threading
import time
from typing import Any

from openrgb.utils import RGBColor

from app import openrgb_client as rgb
from app import store

PREDEFINED = [
    {
        "id": "off",
        "name": "Off",
        "kind": "predefined",
        "adjustments": [],
        "mode_names": ["off", "off / static"],
    },
    {
        "id": "static",
        "name": "Static",
        "kind": "predefined",
        "adjustments": ["color", "brightness"],
        "mode_names": ["static", "solid"],
    },
    {
        "id": "breathing",
        "name": "Breathing",
        "kind": "predefined",
        "adjustments": ["color", "speed", "brightness"],
        "mode_names": ["breathing", "breathe", "pulse"],
    },
    {
        "id": "rainbow",
        "name": "Rainbow",
        "kind": "predefined",
        "adjustments": ["speed", "brightness"],
        "mode_names": ["rainbow", "rainbow wave"],
    },
    {
        "id": "wave",
        "name": "Wave",
        "kind": "predefined",
        "adjustments": ["speed", "brightness"],
        "mode_names": ["wave", "color wave"],
    },
    {
        "id": "spectrum",
        "name": "Spectrum cycle",
        "kind": "predefined",
        "adjustments": ["speed", "brightness"],
        "mode_names": ["spectrum cycle", "spectrum", "color cycle", "cycling"],
    },
]

_anim_stop = threading.Event()
_anim_thread: threading.Thread | None = None
_last_user_mode: dict[str, Any] | None = None


FONT_5X7: dict[str, list[str]] = {
    " ": ["00000"] * 7,
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["01110", "10000", "11110", "10001", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
}


def stop_animation() -> None:
    global _anim_thread
    _anim_stop.set()
    thread = _anim_thread
    if thread and thread.is_alive():
        thread.join(timeout=1.5)
    _anim_thread = None


def _start_animation(target) -> None:
    global _anim_thread
    stop_animation()
    _anim_stop.clear()
    _anim_thread = threading.Thread(target=target, name="rgb-mode-anim", daemon=True)
    _anim_thread.start()


def list_modes() -> dict[str, Any]:
    return {"predefined": PREDEFINED, "custom": store.list_custom_modes()}


def remember_user_mode(body: dict[str, Any]) -> None:
    global _last_user_mode
    _last_user_mode = dict(body)


def last_user_mode() -> dict[str, Any] | None:
    return _last_user_mode


def apply_mode(body: dict[str, Any], remember: bool = True) -> dict[str, Any]:
    mode_id = body.get("mode_id") or "static"
    device_ids = body.get("device_ids")
    color = body.get("color") or "#00a3e0"
    speed = int(body.get("speed") or 50)
    brightness = int(body.get("brightness") if body.get("brightness") is not None else 100)
    if remember:
        remember_user_mode(body)
    stop_animation()
    factor = rgb.effective_brightness(brightness)
    rgb_color = rgb.rgb_from_hex(color, factor)

    predefined = next((m for m in PREDEFINED if m["id"] == mode_id), None)
    if predefined:
        _apply_predefined(predefined, device_ids, rgb_color, speed, factor)
        return {"ok": True, "mode_id": mode_id}

    custom = store.get_custom_mode(mode_id)
    if not custom:
        raise KeyError(f"mode {mode_id} not found")
    if custom["kind"] == "symbol":
        _apply_symbol(custom["payload"], device_ids, rgb_color, speed)
    else:
        _apply_text(custom["payload"], device_ids, rgb_color, speed)
    return {"ok": True, "mode_id": mode_id}


def _apply_predefined(mode: dict[str, Any], device_ids, color: RGBColor, speed: int, factor: float) -> None:
    mode_id = mode["id"]
    devices = rgb.iter_devices(device_ids)
    if mode_id == "off":
        rgb.client_clear()
        return
    for device in devices:
        if mode_id == "static":
            if not rgb.try_set_mode(device, mode["mode_names"]):
                rgb.set_direct_color(device, color)
            else:
                try:
                    device.set_color(color, fast=True)
                except Exception:
                    rgb.set_direct_color(device, color)
            continue
        if rgb.try_set_mode(device, mode["mode_names"], speed=speed):
            try:
                device.set_color(color, fast=True)
            except Exception:
                pass
            continue
        if mode_id == "breathing":
            ids, col, spd = device_ids, color, speed
            _start_animation(lambda: _breathe_loop(ids, col, spd))
            return
        if mode_id in {"rainbow", "spectrum"}:
            ids, spd, fac = device_ids, speed, factor
            _start_animation(lambda: _rainbow_loop(ids, spd, fac))
            return
        if mode_id == "wave":
            ids, col, spd = device_ids, color, speed
            _start_animation(lambda: _wave_loop(ids, col, spd))
            return
        rgb.set_direct_color(device, color)


def _breathe_loop(device_ids, color: RGBColor, speed: int) -> None:
    period = max(0.4, 3.0 - (speed / 50.0))
    t0 = time.time()
    while not _anim_stop.is_set():
        phase = (math.sin((time.time() - t0) * (2 * math.pi / period)) + 1) / 2
        scaled = RGBColor(int(color.red * phase), int(color.green * phase), int(color.blue * phase))
        for device in rgb.iter_devices(device_ids):
            rgb.set_direct_color(device, scaled)
        _anim_stop.wait(0.05)


def _rainbow_loop(device_ids, speed: int, factor: float) -> None:
    t0 = time.time()
    while not _anim_stop.is_set():
        hue = ((time.time() - t0) * (speed / 8.0) * 60) % 360
        color = RGBColor.fromHSV(hue, 100, 100 * factor)
        for device in rgb.iter_devices(device_ids):
            rgb.set_direct_color(device, color)
        _anim_stop.wait(0.05)


def _wave_loop(device_ids, color: RGBColor, speed: int) -> None:
    t0 = time.time()
    while not _anim_stop.is_set():
        offset = (time.time() - t0) * (speed / 20.0)
        for device in rgb.iter_devices(device_ids):
            colors = []
            count = max(1, len(device.leds))
            for i in range(count):
                wave = (math.sin((i / max(1, count)) * math.pi * 2 - offset) + 1) / 2
                colors.append(
                    RGBColor(int(color.red * wave), int(color.green * wave), int(color.blue * wave))
                )
            rgb.set_led_colors(device, colors)
        _anim_stop.wait(0.05)


def _grid_from_payload(payload: dict[str, Any]) -> list[list[int]]:
    grid = payload.get("pixels") or payload.get("grid") or []
    return [[1 if cell else 0 for cell in row] for row in grid]


def _apply_symbol(payload: dict[str, Any], device_ids, color: RGBColor, speed: int) -> None:
    grid = _grid_from_payload(payload)
    if int(payload.get("speed") or speed or 0) > 0 and payload.get("animate"):
        _start_animation(lambda: _symbol_loop(grid, device_ids, color, speed))
        return
    for device in rgb.iter_devices(device_ids):
        rgb.set_led_colors(device, _map_grid(device, grid, color))


def _symbol_loop(grid, device_ids, color: RGBColor, speed: int) -> None:
    t0 = time.time()
    while not _anim_stop.is_set():
        pulse = (math.sin((time.time() - t0) * (speed / 15.0)) + 1) / 2
        scaled = RGBColor(int(color.red * pulse), int(color.green * pulse), int(color.blue * pulse))
        for device in rgb.iter_devices(device_ids):
            rgb.set_led_colors(device, _map_grid(device, grid, scaled))
        _anim_stop.wait(0.05)


def _map_grid(device, grid: list[list[int]], color: RGBColor) -> list[RGBColor]:
    off = RGBColor(0, 0, 0)
    count = len(device.leds)
    colors = [off] * count
    height = len(grid) or 1
    width = len(grid[0]) if grid else 1
    matrix_zone = None
    for zone in device.zones or []:
        if getattr(zone, "matrix_map", None) and zone.mat_width and zone.mat_height:
            matrix_zone = zone
            break
    if matrix_zone and matrix_zone.matrix_map:
        for y, row in enumerate(matrix_zone.matrix_map):
            for x, led_index in enumerate(row):
                if led_index is None or int(led_index) < 0 or int(led_index) >= count:
                    continue
                gy = int(y * height / max(1, matrix_zone.mat_height))
                gx = int(x * width / max(1, matrix_zone.mat_width))
                on = grid[min(gy, height - 1)][min(gx, width - 1)] if grid else 0
                colors[int(led_index)] = color if on else off
        return colors
    for i in range(count):
        gy = int((i / max(1, count)) * height)
        row = grid[min(gy, height - 1)] if grid else []
        gx = i % max(1, width)
        on = row[gx] if gx < len(row) else 0
        colors[i] = color if on else off
    return colors


def _render_text(text: str, offset: int, width: int, height: int) -> list[list[int]]:
    glyph_w = 6
    rows = [""] * 7
    for ch in text.upper():
        glyph = FONT_5X7.get(ch, FONT_5X7[" "])
        for i, line in enumerate(glyph):
            rows[i] += line + "0"
    ribbon = rows
    ribbon_w = max(len(r) for r in ribbon) if ribbon else 1
    grid = []
    for y in range(height):
        src = ribbon[y % 7]
        row = []
        for x in range(width):
            idx = (x + offset) % max(1, ribbon_w + width)
            row.append(1 if idx < len(src) and src[idx] == "1" else 0)
        grid.append(row)
    return grid


def _apply_text(payload: dict[str, Any], device_ids, color: RGBColor, speed: int) -> None:
    text = str(payload.get("text") or "RGB")
    direction = payload.get("direction") or "left"
    scroll_speed = int(payload.get("speed") or speed or 40)
    _start_animation(lambda: _text_loop(text, direction, device_ids, color, scroll_speed))


def _text_loop(text: str, direction: str, device_ids, color: RGBColor, speed: int) -> None:
    offset = 0
    step = 1 if direction != "right" else -1
    delay = max(0.04, 0.25 - (speed / 500.0))
    while not _anim_stop.is_set():
        for device in rgb.iter_devices(device_ids):
            width = max(8, int(math.sqrt(max(1, len(device.leds)))))
            height = max(7, int(math.ceil(len(device.leds) / width)))
            for zone in device.zones or []:
                if getattr(zone, "mat_width", None) and getattr(zone, "mat_height", None):
                    width = int(zone.mat_width)
                    height = int(zone.mat_height)
                    break
            grid = _render_text(text, offset, width, height)
            rgb.set_led_colors(device, _map_grid(device, grid, color))
        offset += step
        _anim_stop.wait(delay)
