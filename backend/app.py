from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from internals.db import KFDatabase
from internals.session import create_session
from internals.tooling import get_env_config, setup_logger
from internals.utils import get_description, get_version, to_boolean
from routes import user

ROOT_DIR = Path(__file__).absolute().parent
env_config = get_env_config()
logger = setup_logger(ROOT_DIR / "logs" / "kidofood.backend.log")
app_ver = get_version()
if app_ver is None:
    logger.error("Failed to get version from pyproject.toml")
    exit(1)
app = FastAPI(
    root_path="/api",
    title="KidoFood",
    description=get_description(),
    version=app_ver,
    license_info={"name": "MIT License", "url": "https://github.com/noaione/kidofood/blob/master/LICENSE"},
    contact={"url": "https://github.com/noaione/kidofood"},
)


@app.on_event("startup")
async def on_app_startup():
    logger.info("Starting up KidoFood backend...")
    logger.info("Connecting to database...")

    DB_URL = env_config.get("MONGODB_URL")
    DB_HOST = env_config.get("MONGODB_HOST")
    DB_PORT = env_config.get("MONGODB_PORT")
    DB_NAME = env_config.get("MONGODB_DBNAME")
    DB_AUTH_STRING = env_config.get("MONGODB_AUTH_STRING")
    DB_AUTH_SOURCE = env_config.get("MONGODB_AUTH_SOURCE")
    DB_AUTH_TLS = to_boolean(env_config.get("MONGODB_TLS"))

    if DB_URL is not None:
        kfdb = KFDatabase(DB_URL)
    elif DB_HOST is not None:
        kfdb = KFDatabase(
            DB_HOST,
            DB_PORT or 27017,
            DB_NAME or "kidofood",
            DB_AUTH_STRING,
            DB_AUTH_SOURCE or "admin",
            DB_AUTH_TLS,
        )
    else:
        raise Exception("No database connection information provided!")

    await kfdb.connect()
    logger.info("Connected to database!")

    logger.info("Creating session...")
    SECRET_KEY = env_config.get("SECRET_KEY") or "KIDOFOOD_SECRET_KEY"
    REDIS_HOST = env_config.get("REDIS_HOST")
    REDIS_PORT = env_config.get("REDIS_PORT")
    REDIS_PASS = env_config.get("REDIS_PASS")
    if REDIS_HOST is None:
        raise Exception("No Redis connection information provided!")
    SESSION_MAX_AGE = int(env_config.get("SESSION_MAX_AGE") or 7 * 24 * 60 * 60)
    create_session(SECRET_KEY, REDIS_HOST, REDIS_PORT, REDIS_PASS, SESSION_MAX_AGE)
    logger.info("Session created!")


app.include_router(
    user.router,
)


@app.get("/")
async def root_api():
    # Redirect to docs
    return RedirectResponse("/docs")
