# rgb-controller-api

Python Starlette + uvicorn for RGB Controller. Lights are driven through [openrgb-python](https://github.com/jath03/openrgb-python) talking to an OpenRGB SDK server.

(The HTTP app uses Starlette, the ASGI core FastAPI is built on, because FastAPI/pydantic has no installable wheel on this Python 3.15 Windows setup without MSVC `link.exe`.)

## Requirements

- Python 3.11+
- OpenRGB running with **SDK Server** enabled
- SQLite file (created automatically)

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8132
```

- Health: `GET /health`
- Listen: **8132**
- Database: `data/rgb-controller.db` (`SQLITE_PATH`)
- Sibling WebUI origin: `http://localhost:5182`

OpenRGB SDK **host and port are set on the Settings page** (defaults `127.0.0.1` and `6742`), not in `.env`.

There is no login.
