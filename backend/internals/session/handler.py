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

import os
from enum import Enum
from typing import Optional, Union
from uuid import UUID

from fastapi import Request, Response
from fastapi.openapi.models import APIKey, APIKeyIn
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pydantic import BaseModel

from .backend import InMemoryBackend, RedisBackend, SessionBackend
from .errors import SessionError
from .models import UserSession

__all__ = (
    "SameSiteEnum",
    "CookieParameters",
    "SessionHandler",
    "create_session_handler",
    "get_session_handler",
    "check_session",
)


class SameSiteEnum(str, Enum):
    lax = "lax"
    strict = "strict"
    none = "none"


class CookieParameters(BaseModel):
    max_age: int = 14 * 24 * 60 * 60  # 14 days in seconds
    path: str = "/"
    domain: Optional[str] = None
    secure: bool = False
    httponly: bool = True
    samesite: SameSiteEnum = SameSiteEnum.lax


class SessionHandler:
    def __init__(
        self,
        *,
        cookie_name: str,
        identifier: str,
        secret_key: str,
        params: CookieParameters,
        scheme_name: Optional[str] = None,
        backend: SessionBackend,
    ):
        self.model: APIKey = APIKey(
            **{"in": APIKeyIn.cookie},  # type: ignore
            name=cookie_name,
        )
        self._identifier = identifier
        self.scheme_name = scheme_name or self.__class__.__name__
        self.signer = URLSafeTimedSerializer(secret_key, salt=cookie_name)
        self.params = params.copy(deep=True)

        self.backend = backend

    async def set_session(self, data: UserSession, response: Optional[Response] = None):
        await self.backend.create(data.session_id, data)
        if response is not None:
            self.set_cookie(response, data.session_id)

    def set_cookie(self, response: Response, session_id: UUID):
        dumps = self.signer.dumps(session_id.hex)
        if isinstance(dumps, bytes):
            dumps = dumps.decode("utf-8")
        response.set_cookie(
            key=self.model.name,
            value=dumps,
            max_age=self.params.max_age,
            path=self.params.path,
            domain=self.params.domain,
            secure=self.params.secure,
            httponly=self.params.httponly,
            samesite=self.params.samesite.value,
        )

    async def remove_session(self, session_id: Union[str, UUID], response: Optional[Response] = None):
        as_uuid = UUID(session_id) if isinstance(session_id, str) else session_id
        await self.backend.delete(as_uuid)
        if response is not None:
            self.remove_cookie(response)

    def remove_cookie(self, response: Response):
        if self.params.domain:
            response.delete_cookie(
                key=self.model.name,
                path=self.params.path,
                domain=self.params.domain,
            )
        else:
            response.delete_cookie(
                key=self.model.name,
                path=self.params.path,
            )

    @property
    def identifier(self) -> str:
        return self._identifier

    async def __call__(self, request: Request):
        signed_session = request.cookies.get(self.model.name)
        if not signed_session:
            raise SessionError(detail="No session found", status_code=403)

        try:
            session = UUID(self.signer.loads(signed_session, max_age=self.params.max_age, return_timestamp=False))
        except (SignatureExpired, BadSignature):
            raise SessionError(detail="Session expired/invalid", status_code=401)

        session_data = await self.backend.read(session)
        if not session_data:
            raise SessionError(detail="Session expired/invalid", status_code=401)
        return session_data


_GLOBAL_SESSION_HANDLER: Optional[SessionHandler] = None


def create_session_handler(
    secret_key: str,
    redis_host: Optional[str] = None,
    redis_port: int = 6379,
    redis_password: Optional[str] = None,
    max_age=7 * 24 * 60 * 60,
):
    global _GLOBAL_SESSION_HANDLER

    backend = InMemoryBackend()
    redis_host = redis_host.strip() if isinstance(redis_host, str) else redis_host
    if redis_host:
        backend = RedisBackend(redis_host, redis_port, redis_password)

    if _GLOBAL_SESSION_HANDLER is None:
        secure = os.getenv("NODE_ENV") == "production"
        cookie_params = CookieParameters(max_age=max_age, secure=secure)
        _GLOBAL_SESSION_HANDLER = SessionHandler(
            cookie_name="kidofood|session",
            identifier="kidofood|ident",
            secret_key=secret_key,
            params=cookie_params,
            backend=backend,
        )


def get_session_handler() -> SessionHandler:
    global _GLOBAL_SESSION_HANDLER

    if _GLOBAL_SESSION_HANDLER is None:
        raise ValueError("Session not created, call create_session first")

    return _GLOBAL_SESSION_HANDLER


async def check_session(request: Request):
    session_handler = get_session_handler()
    return await session_handler(request)
