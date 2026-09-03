from __future__ import annotations

from typing import Any

from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app import idle, modes, openrgb_client as rgb, startup, store
from app.config import WEBUI_ORIGIN


def _error(status: int, detail: str) -> JSONResponse:
    return JSONResponse({"error": detail, "detail": detail}, status_code=status)


async def health(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def openrgb_status(_request: Request) -> JSONResponse:
    return JSONResponse(rgb.status())


async def openrgb_test(request: Request) -> JSONResponse:
    body = await _json(request)
    settings = store.get_settings()
    host = str(body.get("host") or settings["openrgb_host"])
    port = int(body.get("port") or settings["openrgb_port"])
    return JSONResponse(rgb.test_connect(host, port))


async def devices(_request: Request) -> JSONResponse:
    try:
        return JSONResponse({"devices": rgb.list_devices()})
    except Exception as exc:
        return _error(503, str(exc))


async def device_detail(request: Request) -> JSONResponse:
    device_id = int(request.path_params["device_id"])
    try:
        return JSONResponse(rgb.get_device(device_id))
    except KeyError as exc:
        return _error(404, str(exc))
    except Exception as exc:
        return _error(503, str(exc))


async def set_device_mode(request: Request) -> JSONResponse:
    device_id = int(request.path_params["device_id"])
    body = await _json(request)
    name = str(body.get("name") or "")
    if not name:
        return _error(400, "name is required")
    try:
        rgb.set_device_mode(device_id, name)
        return JSONResponse({"ok": True})
    except KeyError as exc:
        return _error(404, str(exc))
    except Exception as exc:
        return _error(503, str(exc))


async def get_modes(_request: Request) -> JSONResponse:
    return JSONResponse(modes.list_modes())


async def apply_mode(request: Request) -> JSONResponse:
    body = await _json(request)
    if not body.get("mode_id"):
        return _error(400, "mode_id is required")
    try:
        return JSONResponse(modes.apply_mode(body))
    except KeyError as exc:
        return _error(404, str(exc))
    except Exception as exc:
        return _error(503, str(exc))


async def create_custom(request: Request) -> JSONResponse:
    body = await _json(request)
    kind = str(body.get("kind") or "")
    name = str(body.get("name") or "")
    payload = body.get("payload") or {}
    if kind not in {"symbol", "text"}:
        return _error(400, "kind must be symbol or text")
    if not name:
        return _error(400, "name is required")
    if not isinstance(payload, dict):
        return _error(400, "payload must be an object")
    return JSONResponse(store.create_custom_mode(kind, name, payload))


async def update_custom(request: Request) -> JSONResponse:
    mode_id = str(request.path_params["mode_id"])
    body = await _json(request)
    kind = str(body.get("kind") or "")
    name = str(body.get("name") or "")
    payload = body.get("payload") or {}
    updated = store.update_custom_mode(mode_id, kind, name, payload if isinstance(payload, dict) else {})
    if not updated:
        return _error(404, "custom mode not found")
    return JSONResponse(updated)


async def delete_custom(request: Request) -> JSONResponse:
    mode_id = str(request.path_params["mode_id"])
    if not store.delete_custom_mode(mode_id):
        return _error(404, "custom mode not found")
    return JSONResponse({"ok": True})


async def get_settings(_request: Request) -> JSONResponse:
    return JSONResponse(store.get_settings())


async def put_settings(request: Request) -> JSONResponse:
    body = await _json(request)
    before = store.get_settings()
    if "idle_mode_id" in body or "idle_minutes" in body:
        merged = {**before, **body}
        has_mode = bool(str(merged.get("idle_mode_id") or "").strip())
        try:
            minutes = int(merged.get("idle_minutes") or 0)
        except (TypeError, ValueError):
            return _error(400, "time-of-idle must be a number of minutes")
        if has_mode and minutes < 1:
            return _error(400, "Idle needs both time-of-idle (minutes) and a mode")
        if minutes >= 1 and not has_mode:
            return _error(400, "Idle needs both time-of-idle (minutes) and a mode")
    after = store.update_settings(body)
    host_changed = after["openrgb_host"] != before["openrgb_host"] or int(after["openrgb_port"]) != int(
        before["openrgb_port"]
    )
    if host_changed:
        try:
            rgb.connect(after["openrgb_host"], int(after["openrgb_port"]))
        except Exception:
            pass
    if "run_startup" in body or "openrgb_exe_path" in body:
        try:
            startup.set_run_startup(bool(after["run_startup"]), after.get("openrgb_exe_path") or "")
        except Exception as exc:
            return _error(500, f"startup task: {exc}")
    if "backlight_percent" in body:
        last = modes.last_user_mode()
        if last:
            try:
                modes.apply_mode(last, remember=False)
            except Exception:
                pass
    return JSONResponse(after)


async def _json(request: Request) -> dict[str, Any]:
    if not request.headers.get("content-type", "").startswith("application/json"):
        try:
            data = await request.json()
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}
    try:
        data = await request.json()
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


@asynccontextmanager
async def lifespan(_app: Starlette):
    idle.start()
    try:
        rgb.connect()
    except Exception:
        pass
    yield


routes = [
    Route("/health", health),
    Route("/api/v1/openrgb/status", openrgb_status),
    Route("/api/v1/openrgb/test", openrgb_test, methods=["POST"]),
    Route("/api/v1/devices", devices),
    Route("/api/v1/devices/{device_id:int}", device_detail),
    Route("/api/v1/devices/{device_id:int}/mode", set_device_mode, methods=["POST"]),
    Route("/api/v1/modes", get_modes, methods=["GET", "PUT"]),
    Route("/api/v1/modes/apply", apply_mode, methods=["POST"]),
    Route("/api/v1/modes/custom", create_custom, methods=["POST"]),
    Route("/api/v1/modes/custom/{mode_id}", update_custom, methods=["PUT"]),
    Route("/api/v1/modes/custom/{mode_id}", delete_custom, methods=["DELETE"]),
    Route("/api/v1/settings", get_settings),
    Route("/api/v1/settings", put_settings, methods=["PUT"]),
]

app = Starlette(
    debug=False,
    routes=routes,
    lifespan=lifespan,
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=[WEBUI_ORIGIN, "http://localhost:5182", "http://127.0.0.1:5182"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ],
)
