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

from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.datastructures import Default
from fastapi.responses import RedirectResponse
from strawberry.printer import print_schema
from strawberry.fastapi import GraphQLRouter

from internals.db import KFDatabase
from internals.discover import discover_routes
from internals.graphql import schema, KidoFoodContext
from internals.responses import ORJSONXResponse, ResponseType
from internals.session import SessionError, create_session_handler, get_session_handler, check_session
from internals.storage import create_s3_server, get_s3_or_local
from internals.tooling import get_env_config, setup_logger
from internals.utils import get_description, get_version, to_boolean, try_int

ROOT_DIR = Path(__file__).absolute().parent
env_config = get_env_config()
logger = setup_logger(ROOT_DIR / "logs" / "kidofood.backend.log")
app_ver = get_version()
if app_ver is None:
    logger.error("Failed to get version from pyproject.toml")
    exit(1)
app = FastAPI(
    title="KidoFood",
    description=get_description(),
    version=app_ver,
    license_info={"name": "MIT License", "url": "https://github.com/noaione/kidofood/blob/master/LICENSE"},
    contact={"url": "https://github.com/noaione/kidofood"},
)
router = APIRouter(prefix="/api")


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
        kfdb = KFDatabase(DB_URL, dbname=DB_NAME or "kidofood")
    elif DB_HOST is not None:
        kfdb = KFDatabase(
            DB_HOST,
            try_int(DB_PORT) or 27017,
            DB_NAME or "kidofood",
            DB_AUTH_STRING,
            DB_AUTH_SOURCE or "admin",
            DB_AUTH_TLS,
        )
    else:
        raise Exception("No database connection information provided!")

    await kfdb.connect()
    logger.info("Connected to database!")

    S3_HOSTNAME = env_config.get("S3_HOSTNAME")
    S3_ACCESS_KEY = env_config.get("S3_ACCESS_KEY")
    S3_SECRET_KEY = env_config.get("S3_SECRET_KEY")
    S3_BUCKET = env_config.get("S3_BUCKET")

    # S3 all available?
    if S3_HOSTNAME is not None and S3_ACCESS_KEY is not None and S3_SECRET_KEY is not None and S3_BUCKET is not None:
        logger.info("S3 storage available, connecting...")
        await create_s3_server(S3_HOSTNAME, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET)
        logger.info("Connected to S3 storage!")
    else:
        logger.info("S3 storage not available, using local storage instead.")

    logger.info("Creating session...")
    SECRET_KEY = env_config.get("SECRET_KEY") or "KIDOFOOD_SECRET_KEY"
    REDIS_HOST = env_config.get("REDIS_HOST")
    REDIS_PORT = env_config.get("REDIS_PORT")
    REDIS_PASS = env_config.get("REDIS_PASS")
    if REDIS_HOST is None:
        raise Exception("No Redis connection information provided!")
    SESSION_MAX_AGE = int(env_config.get("SESSION_MAX_AGE") or 7 * 24 * 60 * 60)
    create_session_handler(SECRET_KEY, REDIS_HOST, try_int(REDIS_PORT) or 6379, REDIS_PASS, SESSION_MAX_AGE)
    logger.info("Session created!")


@app.on_event("shutdown")
async def on_app_shutdown():
    logger.info("Shutting down KidoFood backend...")
    s3_local = get_s3_or_local()
    logger.info("Closing storage connection...")
    s3_local.close()
    logger.info("Closed storage connection!")

    try:
        logger.info("Closing redis session backend...")
        session_handler = get_session_handler()
        await session_handler.backend.shutdown()
        logger.info("Closed redis session backend!")
    except Exception:
        pass


@app.exception_handler(SessionError)
async def session_exception_handler(_: Request, exc: SessionError):
    status_code = exc.status_code
    if status_code < 400:
        status_code = 403
    return ResponseType(error=exc.detail, code=status_code).to_orjson(status_code)


async def gql_user_context(request: Request):
    try:
        session = await check_session(request)
        return KidoFoodContext(user=session)
    except Exception:
        return KidoFoodContext()


async def get_context(
    custom_context=Depends(gql_user_context),
):
    return custom_context


ORJSONDefault = Default(ORJSONXResponse)
# Auto add routes using discovery
discover_routes(router, ROOT_DIR / "routes", recursive=True, default_response_class=ORJSONDefault)
graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
)
app.include_router(router)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/", include_in_schema=False)
async def root_api():
    # Redirect to docs
    return RedirectResponse("/docs")


if __name__ == "__main__":
    print(print_schema(schema))
