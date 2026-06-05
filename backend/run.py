"""
Main entry point for starting the FastAPI application and automatically opening
the dashboard in the browser.
"""

import logging
import os
import sys
import webbrowser
from threading import Timer

import uvicorn
from dotenv import load_dotenv

# Ensure the backend directory is in python search path and is the working directory
backend_dir = os.path.abspath(os.path.dirname(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

# Load any custom env vars from .env
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def open_browser() -> None:
    """Automatically open the browser to the web dashboard after server starts."""
    if os.getenv("SKIP_BROWSER", "false").lower() in ("true", "1", "yes"):
        return
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")
    url = f"http://{host}:{port}/"
    logger.info(f"[BROWSER_OPEN] Url: {url}")
    webbrowser.open(url)


if __name__ == "__main__":
    server_port = int(os.getenv("PORT", "8000"))
    server_host = os.getenv("HOST", "127.0.0.1")

    # Schedule browser opening in 1.5 seconds
    Timer(1.5, open_browser).start()

    logger.info(f"[SERVER_START] Host: {server_host} | Port: {server_port}")
    uvicorn.run("app:app", host=server_host, port=server_port, reload=True)
