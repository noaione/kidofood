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
from strawberry.file_uploads import Upload

from internals.db import Merchant as MerchantDB
from internals.db import User as UserDB
from internals.enums import AvatarType
from internals.session.models import UserSession
from internals.utils import make_uuid, to_uuid

from ..enums import UserTypeGQL
from .common import AvatarImageGQL
from .merchant import MerchantGQL

__all__ = (
    "UserGQL",
    "UserInputGQL",
)


@gql.type(name="User", description="User model")
class UserGQL:
    id: UUID = gql.field(description="The ID of the User")
    name: str = gql.field(description="The client or user real name")
    email: str = gql.field(description="The client or user email")
    type: UserTypeGQL = gql.field(description="The user type")
    avatar: Optional[AvatarImageGQL] = gql.field(description="The user avatar")
    merchant_id: gql.Private[Optional[str]]
    user_id: gql.Private[str]  # ObjectId

    @gql.field(description="The associated merchant information if type is MERCHANT")
    async def merchant(self) -> Optional[MerchantGQL]:
        # Resolve merchant
        if self.merchant_id is None:
            return None
        merchant = await MerchantDB.find_one(MerchantDB.id == ObjectId(self.merchant_id))
        if merchant is None:
            return None
        return MerchantGQL.from_db(merchant)

    @classmethod
    def from_db(cls, user: UserDB):
        merchant_id = None  # type: Optional[str]
        if user.merchant is not None:
            if isinstance(user.merchant, MerchantDB):
                merchant_id = str(user.merchant.id)
            else:
                merchant_id = str(user.merchant.ref.id)
        avatar = None  # type: Optional[AvatarImageGQL]
        if user.avatar and user.avatar.key:
            avatar = AvatarImageGQL.from_db(user.avatar, AvatarType.USERS)
        return cls(
            id=user.user_id,
            name=user.name,
            email=user.email,
            type=user.type,
            avatar=avatar,
            merchant_id=merchant_id,
            user_id=str(user.id),
        )

    @classmethod
    def from_session(cls, user: UserSession):
        avatar = None  # type: Optional[AvatarImageGQL]
        if user.avatar:
            avatar = AvatarImageGQL(name=user.avatar, type=AvatarType.USERS)
        return cls(
            id=to_uuid(user.user_id),
            name=user.name,
            email=user.email,
            type=user.type,
            avatar=avatar,
            merchant_id=user.merchant_info,
            user_id=user.user_db,
        )

    def to_session(self):
        return UserSession(
            user_id=str(self.id),
            name=self.name,
            email=self.email,
            type=self.type,
            avatar=self.avatar.name if self.avatar else None,
            merchant_info=self.merchant_id,
            user_db=self.user_id,
            remember_me=True,
            remember_latch=False,
            session_id=make_uuid(False),
        )


@gql.type(name="UserInput", description="User update data information (all fields are optional.)")
class UserInputGQL:
    name: Optional[str] = gql.field(description="The client or user real name", default=gql.UNSET)
    avatar: Optional[Upload] = gql.field(description="The user avatar", default=gql.UNSET)
    password: Optional[str] = gql.field(description="The old password", default=gql.UNSET)
    new_password: Optional[str] = gql.field(description="The new password", default=gql.UNSET)

    def is_unset(self) -> bool:
        # Check if all fields are either unset or None
        return all(
            getattr(self, field.name) in (gql.UNSET, None)
            for field in self.__class__._type_definition.fields  # type: ignore (gql.input is a dataclass format)
        )
