from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING, Generic, Optional

import orjson
from fastapi import HTTPException
from fastapi_sessions.backends.session_backend import (BackendError,
                                                       SessionBackend,
                                                       SessionModel)
from fastapi_sessions.frontends.implementations import (CookieParameters,
                                                        SessionCookie)
from fastapi_sessions.frontends.session_frontend import ID
from fastapi_sessions.session_verifier import SessionVerifier
from pydantic import BaseModel

from .db import UserType
from .redbridge import RedisBridge

if TYPE_CHECKING:
    from starlette.requests import Request

__all__ = (
    "UserSession",
    "RedisBackend",
    "SharedSessionHandler",
    "create_session",
    "get_session_verifier",
    "get_session_cookie",
)


class UserSession(BaseModel):
    # UUID string
    user_id: str
    email: str
    name: str
    type: UserType

    # RememberMe
    remember_me: bool
    remember_latch: bool
    session_id: str


class RedisBackend(Generic[ID, SessionModel], SessionBackend[ID, SessionModel]):
    """Store session data in a redis database."""

    def __init__(
        self,
        host: str,
        port: int = 6379,
        password: Optional[str] = None,
        *,
        key_prefix: str = "kidofood:session:",
    ):
        """Initialize a new redis database."""
        self._client = RedisBridge(host, port, password)
        self._key_prefix = key_prefix

    async def _before_operation(self):
        """Connect to the database before performing an operation."""
        if not self._client.is_connected:
            await self._client.connect()
            try:
                await self._client.get("pingpong")
            except ConnectionRefusedError as ce:
                raise BackendError("Connection to redis failed") from ce

    async def _check_key(self, session_id: ID) -> bool:
        """Check if a key exists."""
        return await self._client.exists(self._key_prefix + session_id)

    def _dump_json(self, data: SessionModel) -> str:
        return orjson.dumps(
            data.dict(), option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_SERIALIZE_UUID
        ).decode()

    async def create(self, session_id: ID, data: SessionModel) -> None:
        await self._before_operation()
        if await self._check_key(session_id):
            raise BackendError("create can't overwrite an existing session")

        await self._client.set(self._key_prefix + str(session_id), self._dump_json(data.copy(deep=True)))

    async def read(self, session_id: ID) -> Optional[SessionModel]:
        await self._before_operation()
        data = await self._client.get(self._key_prefix + str(session_id))
        if not data:
            return
        data_json = orjson.loads(data)

        return UserSession.parse_obj(data_json)

    async def update(self, session_id: ID, data: SessionModel) -> None:
        await self._before_operation()
        if not await self._check_key(session_id):
            raise BackendError("session does not exist, cannot update")

        await self._client.set(self._key_prefix + str(session_id), self._dump_json(data.copy(deep=True)))

    async def delete(self, session_id: ID) -> None:
        await self._before_operation()
        await self._client.rm(self._key_prefix + str(session_id))


# Make a shared session between different route file
class SharedSessionHandler(SessionVerifier[str, UserSession]):
    def __init__(
        self,
        *,
        identifier: str,
        auto_error: bool,
        backend: RedisBackend[str, UserSession],
        auth_http_exception: HTTPException,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = backend
        self._auth_http_exception = auth_http_exception

        self._loop = loop or asyncio.get_event_loop()

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    def verify_session(self, model: UserSession) -> bool:
        if model.remember_me is False and model.remember_latch is True:
            self._loop.run_until_complete(self._backend.delete(model.session_id))
            return False
        elif model.remember_me is False and model.remember_latch is False:
            model.remember_latch = True
            self._loop.run_until_complete(self._backend.update(model.session_id, model))
            return True

        return True


_SESSION_COOKIE: SessionCookie = None
_SESSION_HANDLER: SharedSessionHandler = None


def create_session(
    secret_key: str,
    redis_host: str,
    redis_port: int = 6379,
    redis_password: Optional[str] = None,
    max_age=7 * 24 * 60 * 60,
):
    global _SESSION_HANDLER
    global _SESSION_COOKIE
    if _SESSION_COOKIE is None:
        secure = os.getenv("NODE_ENV") == "production"
        cookie_params = CookieParameters(max_age=max_age, secure=secure)
        _SESSION_COOKIE = SessionCookie(
            cookie_name="kidofood/session",
            identifier="kidofood/ident",
            auto_error=True,
            secret_key=secret_key,
            cookie_params=cookie_params,
        )

    if _SESSION_HANDLER is None:
        _SESSION_HANDLER = SharedSessionHandler(
            identifier="kidofood/ident",
            auto_error=True,
            backend=RedisBackend(redis_host, redis_port, redis_password),
            auth_http_exception=HTTPException(
                status_code=403,
                detail="Invalid session",
            ),
        )


async def get_session_verifier(request: Request):
    if _SESSION_HANDLER is None:
        raise ValueError("Session not created, call create_session first")
    return await _SESSION_HANDLER(request)


async def get_session_cookie(request: Request):
    if _SESSION_COOKIE is None:
        raise ValueError("Session not created, call create_session first")
    return await _SESSION_COOKIE(request)
