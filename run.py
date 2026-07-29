"""Run the Propongo development server."""

import os
import subprocess
import sys

from app.config import Config

PORT = Config.PORT

subprocess.run(
    ["fuser", "-k", f"{PORT}/tcp"],
    capture_output=True,
)

if os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes"):
    os.environ["FLASK_DEBUG"] = "1"

from app.main import run_server

run_server()
