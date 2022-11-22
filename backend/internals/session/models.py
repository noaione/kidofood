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

from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from internals.db.models import User, UserType
from internals.utils import make_uuid

__all__ = (
    "PartialUserSession",
    "UserSession",
)


class PartialUserSession(BaseModel):
    # UUID string
    user_id: str
    email: str
    name: str
    type: UserType
    avatar: Optional[str]

    @classmethod
    def from_db(cls, user: User):
        avatar = None
        if user.avatar and user.avatar.key:
            avatar = f"{user.avatar.key}.{user.avatar.format}"
        return cls(
            user_id=str(user.user_id),
            email=user.email,
            name=user.name,
            type=user.type,
            avatar=avatar,
        )


class UserSession(PartialUserSession):
    user_db: str  # ObjectId, stringified
    merchant_info: Optional[str] = None
    # RememberMe
    remember_me: bool
    remember_latch: bool
    session_id: UUID

    def to_partial(self) -> PartialUserSession:
        return PartialUserSession(
            user_id=self.user_id,
            email=self.email,
            name=self.name,
            type=self.type,
            avatar=self.avatar,
        )

    @classmethod
    def from_db(cls, user: User, remember: bool = False):
        merchant_id: Optional[str] = None
        if user.merchant is not None:
            merchant_id = str(user.merchant.ref.id)
        avatar = None
        if user.avatar and user.avatar.key:
            avatar = f"{user.avatar.key}.{user.avatar.format}"
        return cls(
            user_id=str(user.user_id),
            email=user.email,
            name=user.name,
            type=user.type,
            avatar=avatar,
            user_db=str(user.id),
            merchant_info=merchant_id,
            remember_me=remember,
            remember_latch=False,
            session_id=make_uuid(False),
        )
