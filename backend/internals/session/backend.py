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

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

import orjson

from ..redbridge import RedisBridge
from .errors import BackendError
from .models import UserSession

__all__ = (
    "InMemoryBackend",
    "RedisBackend",
)


class SessionBackend(ABC):
    """
    Session backend interface
    """

    @abstractmethod
    async def shutdown(self) -> None:
        """Close the connection to the database."""
        pass

    @abstractmethod
    async def create(self, session_id: UUID, data: UserSession) -> None:
        """
        Create new session data on the backend.

        Parameters
        ----------
        session_id : UUID
            The session ID to be created
        data : UserSession
            The user session information

        Raises
        ------
        BackendError
            If the session ID already exist on the backend
        """
        raise NotImplementedError

    @abstractmethod
    async def read(self, session_id: UUID) -> Optional[UserSession]:
        """
        Read or fetch session data from the backend.

        Parameters
        ----------
        session_id : UUID
            The session ID to be fetched

        Returns
        -------
        Optional[UserSession]
            The session if exist on the backend
        """
        raise NotImplementedError

    @abstractmethod
    async def update(self, session_id: UUID, data: UserSession) -> None:
        """
        Update session data on the backend.

        Parameters
        ----------
        session_id : UUID
            The session ID to be updated
        data : UserSession
            The user session information

        Raises
        ------
        BackendError
            If the session ID does not exist on the backend
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, session_id: UUID) -> None:
        """
        Delete session data from the backend.

        Parameters
        ----------
        session_id : UUID
            The session ID to be deleted
        """
        raise NotImplementedError


class InMemoryBackend(SessionBackend):
    """Store session inside a memory dictionary."""

    def __init__(self) -> None:
        self.__SESSIONS: dict[UUID, UserSession] = {}

    async def shutdown(self) -> None:
        pass

    async def read(self, session_id: UUID) -> Optional[UserSession]:
        return self.__SESSIONS.get(session_id)

    async def create(self, session_id: UUID, data: UserSession) -> None:
        if self.__SESSIONS.get(session_id) is not None:
            raise BackendError("create can't overwrite an existing session")
        self.__SESSIONS[session_id] = data

    async def update(self, session_id: UUID, data: UserSession) -> None:
        if self.__SESSIONS.get(session_id) is None:
            raise BackendError("session does not exist, cannot update")
        self.__SESSIONS[session_id] = data

    async def delete(self, session_id: UUID) -> None:
        try:
            del self.__SESSIONS[session_id]
        except KeyError:
            pass


class RedisBackend(SessionBackend):
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

    async def shutdown(self) -> None:
        """Close the connection to the database."""
        await self._client.close()

    async def _before_operation(self):
        """Connect to the database before performing an operation."""
        if not self._client.is_connected:
            await self._client.connect()
            try:
                await self._client.get("pingpong")
            except ConnectionRefusedError as ce:
                raise BackendError("Connection to redis failed") from ce

    async def _check_key(self, session_id: UUID) -> bool:
        """Check if a key exists."""
        return await self._client.exists(self._key_prefix + str(session_id))

    def _dump_json(self, data: UserSession) -> str:
        return orjson.dumps(data.dict(), option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_SERIALIZE_UUID).decode()

    async def create(self, session_id: UUID, data: UserSession) -> None:
        await self._before_operation()
        if await self._check_key(session_id):
            raise BackendError("create can't overwrite an existing session")

        await self._client.set(self._key_prefix + str(session_id), self._dump_json(data.copy(deep=True)))

    async def read(self, session_id: UUID) -> Optional[UserSession]:
        await self._before_operation()
        data = await self._client.get(self._key_prefix + str(session_id))
        if not data:
            return
        return UserSession.parse_obj(data)

    async def update(self, session_id: UUID, data: UserSession) -> None:
        await self._before_operation()
        if not await self._check_key(session_id):
            raise BackendError("session does not exist, cannot update")

        await self._client.set(self._key_prefix + str(session_id), self._dump_json(data.copy(deep=True)))

    async def delete(self, session_id: UUID) -> None:
        await self._before_operation()
        await self._client.rm(self._key_prefix + str(session_id))
