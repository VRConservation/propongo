"""Run the Propongo development server."""

import os
import subprocess
import sys

from app.config import Config

PORT = Config.PORT

# The debug reloader re-executes this script in a child process on every file
# change. Only free the port from the initial process, otherwise the reloader
# child would kill the very server it is restarting.
if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
    subprocess.run(
        ["fuser", "-k", f"{PORT}/tcp"],
        capture_output=True,
    )

if os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes"):
    os.environ["FLASK_DEBUG"] = "1"

from app.main import run_server

run_server()
