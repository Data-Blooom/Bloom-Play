import sys
import time
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import api.state
from engine import get_all_stats
from collectors.gpu import init_gpu
from collectors.network import start_ping_thread
from collectors.hardware import get_hardware_info


app = FastAPI(title="BloomPlay API")


if getattr(sys, "frozen", False):
    # Running from PyInstaller EXE
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

dashboard_dir = BASE_DIR / "dashboard"


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_gpu()
    start_ping_thread()


@app.get("/stats")
def stats():
    api.state.last_client_seen = time.time()
    return get_all_stats()

@app.get("/hardware")
def hardware():
    api.state.last_client_seen = time.time()
    return get_hardware_info()


if dashboard_dir.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(dashboard_dir)),
        name="static"
    )


@app.get("/")
def dashboard():

    index_file = dashboard_dir / "index.html"

    if not index_file.exists():
        return {
            "error": "dashboard/index.html not found",
            "dashboard_path": str(index_file)
        }

    return FileResponse(index_file)