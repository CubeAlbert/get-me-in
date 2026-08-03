"""Operating-system implementation of explicit frontend actions."""

import os
import platform
import subprocess
from pathlib import Path


class OSFrontend:
    def open_file(self, path: Path) -> None:
        system = platform.system()
        if system == "Windows":
            os.startfile(path)
            return
        command = ["open", str(path)] if system == "Darwin" else ["xdg-open", str(path)]
        subprocess.run(command, check=True)
