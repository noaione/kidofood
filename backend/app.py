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

from fastapi import APIRouter, Depends, FastAPI, Request, WebSocket
from fastapi.datastructures import Default
from fastapi.responses import RedirectResponse
from strawberry.printer import print_schema
from internals.claim import get_claim_status

from internals.db import KFDatabase
from internals.discover import discover_routes
from internals.graphql import KidoFoodContext, KidoGraphQLRouter, schema
from internals.pubsub import get_pubsub
from internals.responses import ORJSONXResponse, ResponseType
from internals.session import SessionError, check_session, create_session_handler, get_session_handler
from internals.storage import get_local_storage
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

    claim_stat = get_claim_status()
    logger.info("Checking claim status...")
    await claim_stat.set_from_db()
    logger.info("Claim status checked!")

    logger.info("Preparing storages system...")
    local_stor = get_local_storage()
    await local_stor.start()
    logger.info("Storages system ready!")

    logger.info("Creating session...")
    SECRET_KEY = env_config.get("SECRET_KEY") or "KIDOFOOD_SECRET_KEY"
    REDIS_HOST = env_config.get("REDIS_HOST")
    REDIS_PORT = env_config.get("REDIS_PORT")
    REDIS_PASS = env_config.get("REDIS_PASS")
    if SECRET_KEY == "KIDOFOOD_SECRET_KEY":
        logger.warning("Using default secret key, please change it later since it's not secure!")
    SESSION_MAX_AGE = int(env_config.get("SESSION_MAX_AGE") or 7 * 24 * 60 * 60)
    create_session_handler(SECRET_KEY, REDIS_HOST, try_int(REDIS_PORT) or 6379, REDIS_PASS, SESSION_MAX_AGE)
    logger.info("Session created!")


@app.on_event("shutdown")
async def on_app_shutdown():
    logger.info("Shutting down KidoFood backend...")
    logger.info("Closed storage connection!")
    pubsub = get_pubsub()
    logger.info("Closing pubsub connection...")
    await pubsub.close()
    logger.info("Closed pubsub connection!")

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


async def gql_user_context(request: Request = None, websocket: WebSocket = None):  # type: ignore
    session = get_session_handler()
    try:
        user = await check_session(request or websocket)
        return KidoFoodContext(session=session, user=user)
    except Exception:
        return KidoFoodContext(session=session)


async def get_context(
    custom_context=Depends(gql_user_context),
):
    claim_stat = get_claim_status()
    if not claim_stat.is_claimed:
        raise Exception("This server is not claimed yet!")
    return custom_context


ORJSONDefault = Default(ORJSONXResponse)
# Auto add routes using discovery
discover_routes(router, ROOT_DIR / "routes", recursive=True, default_response_class=ORJSONDefault)
graphql_app = KidoGraphQLRouter(
    schema,
    context_getter=get_context,
)
app.include_router(router)
app.include_router(graphql_app, prefix="/graphql", include_in_schema=False)


@app.get("/", include_in_schema=False)
async def root_api():
    # Redirect to docs
    return RedirectResponse("/docs")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest="cmd")
    subparser.add_parser("generate-schema")
    args = parser.parse_args()

    if args.cmd == "generate-schema":
        schematics = print_schema(schema)
        schema_file = ROOT_DIR / "schema.graphql"
        with open(schema_file, "wb") as fp:
            fp.write(schematics.encode("utf-8") + b"\n")
        print(f"Schema generated at {schema_file}")
    else:
        print("Unknown command, exiting...")
