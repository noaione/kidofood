from pathlib import Path
from fastapi import FastAPI

from internals.tooling import get_env_config, setup_logger

ROOT_DIR = Path(__file__).absolute().parent
env_config = get_env_config()
logger = setup_logger(ROOT_DIR / "logs" / "kidofood.backend.log")
app = FastAPI()
