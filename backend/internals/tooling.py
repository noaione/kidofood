"""
MIT License

Copyright (c) 2022-present noaione

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import glob
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

import coloredlogs
from dotenv.main import DotEnv

__all__ = (
    "RollingFileHandler",
    "setup_logger",
    "load_env",
    "get_env_config",
)


class RollingFileHandler(RotatingFileHandler):
    """
    A log file handler that follows the same format as RotatingFileHandler,
    but automatically roll over to the next numbering without needing to worry
    about maximum file count or something.

    At startup, we check the last file in the directory and start from there.
    """

    maxBytes: int  # to force mypy to stop complaining????

    def __init__(
        self,
        filename: os.PathLike,
        mode: str = "a",
        maxBytes: int = 0,
        backupCount: int = 0,
        encoding: Optional[str] = None,
        delay: bool = False,
    ) -> None:
        self._last_backup_count = 0
        super().__init__(
            filename, mode=mode, maxBytes=maxBytes, backupCount=backupCount, encoding=encoding, delay=delay
        )
        self.maxBytes = maxBytes
        self.backupCount = backupCount
        self._determine_start_count()

    def _determine_start_count(self):
        all_files = glob.glob(self.baseFilename + "*")
        if all_files:
            all_files.sort()
            last_digit = all_files[-1].split(".")[-1]
            if last_digit.isdigit():
                self._last_backup_count = int(last_digit)

    def doRollover(self) -> None:
        if self.stream and not self.stream.closed:
            self.stream.close()
        self._last_backup_count += 1
        next_name = "%s.%d" % (self.baseFilename, self._last_backup_count)
        self.rotate(self.baseFilename, next_name)
        if not self.delay:
            self.stream = self._open()


def setup_logger(log_path: Path):
    log_path.parent.mkdir(exist_ok=True)

    file_handler = RollingFileHandler(log_path, maxBytes=5_242_880, backupCount=5, encoding="utf-8")
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[file_handler],
        format="[%(asctime)s] - (%(name)s)[%(levelname)s](%(funcName)s): %(message)s",  # noqa: E501
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger()
    coloredlogs.install(
        fmt="[%(asctime)s %(hostname)s][%(levelname)s] (%(name)s[%(process)d]): %(funcName)s: %(message)s",
        level=logging.INFO,
        logger=logger,
        stream=sys.stdout,
    )

    # Set default logging for some modules
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("uvicorn.asgi").setLevel(logging.INFO)
    logging.getLogger("websockets").setLevel(logging.WARNING)

    # Set back to the default of INFO even if asyncio's debug mode is enabled.
    logging.getLogger("asyncio").setLevel(logging.INFO)

    return logger


def load_env(env_path: Path):
    """Load an environment file and set it to the environment table

    Returns the environment dict loaded from the dictionary.
    """
    if not env_path.exists():
        return {}
    env = DotEnv(env_path, stream=None, verbose=False, encoding="utf-8", interpolate=True, override=True)
    env.set_as_environment_variables()

    return env.dict()


def get_env_config():
    """Get the configuration from multiple .env file!"""
    current_dir = Path(__file__).absolute().parent
    backend_dir = current_dir.parent
    root_dir = backend_dir.parent
    frontend_dir = root_dir / "frontend"

    # .env file from every directory
    # variant: .env.local, .env.production, .env.development
    # load depends on the current environment (for production and development)

    NODE_ENV = os.getenv("NODE_ENV", "development")
    is_prod = NODE_ENV == "production"

    env_root = load_env(root_dir / ".env")
    env_front = load_env(frontend_dir / ".env")
    env_back = load_env(backend_dir / ".env")

    # .env.local
    env_root_local = load_env(root_dir / ".env.local")
    env_front_local = load_env(frontend_dir / ".env.local")
    env_back_local = load_env(backend_dir / ".env.local")

    # .env.production
    env_root_prod = load_env(root_dir / ".env.production") if is_prod else {}
    env_front_prod = load_env(frontend_dir / ".env.production") if is_prod else {}
    env_back_prod = load_env(backend_dir / ".env.production") if is_prod else {}

    # .env.development
    env_root_dev = load_env(root_dir / ".env.development") if not is_prod else {}
    env_front_dev = load_env(frontend_dir / ".env.development") if not is_prod else {}
    env_back_dev = load_env(backend_dir / ".env.development") if not is_prod else {}

    # priority: .env.local > .env.production > .env.development > .env
    env_merged = {
        **env_root,
        **env_front,
        **env_back,
        **env_root_local,
        **env_front_local,
        **env_back_local,
        **env_root_prod,
        **env_front_prod,
        **env_back_prod,
        **env_root_dev,
        **env_front_dev,
        **env_back_dev,
    }
    return env_merged
