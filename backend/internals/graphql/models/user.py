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

import strawberry as gql
from bson import ObjectId

from internals.db import Merchant as MerchantDB
from internals.db import User as UserDB
from internals.enums import AvatarType, UserType
from internals.session.models import UserSession
from internals.utils import to_uuid

from .common import AvatarImage
from .merchant import Merchant

__all__ = ("User",)


@gql.type
class User:
    id: UUID = gql.field(description="The ID of the User")
    name: str = gql.field(description="The client or user real name")
    email: str = gql.field(description="The client or user email")
    type: gql.enum(UserType, description="The user type") = gql.field(description="The user type")  # type: ignore
    avatar: Optional[AvatarImage] = gql.field(description="The user avatar")
    merchant_id: gql.Private[Optional[str]]

    @gql.field(description="The associated merchant information if type is MERCHANT")
    async def merchant(self) -> Optional[Merchant]:
        # Resolve merchant
        if self.merchant_id is None:
            return None
        merchant = await MerchantDB.find_one(MerchantDB.id == ObjectId(self.merchant_id))
        if merchant is None:
            return None
        return Merchant.from_db(merchant)

    @classmethod
    def from_db(cls, user: UserDB):
        merchant_id = None  # type: Optional[str]
        if user.merchant is not None:
            merchant_id = str(user.merchant.ref.id)
        avatar = None  # type: Optional[AvatarImage]
        if user.avatar and user.avatar.key:
            avatar = AvatarImage.from_db(user.avatar, AvatarType.USERS)
        return cls(
            id=user.user_id,
            name=user.name,
            email=user.email,
            type=user.type,
            avatar=avatar,
            merchant_id=merchant_id,
        )

    @classmethod
    def from_session(cls, user: UserSession):
        avatar = None  # type: Optional[AvatarImage]
        if user.avatar:
            avatar = AvatarImage(name=user.avatar, type=AvatarType.USERS)
        return cls(
            id=to_uuid(user.user_id),
            name=user.name,
            email=user.email,
            type=user.type,
            avatar=avatar,
            merchant_id=user.merchant_info,
        )
