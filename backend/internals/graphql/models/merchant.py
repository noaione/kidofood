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

from datetime import datetime
from typing import Optional, Type
from uuid import UUID

import strawberry as gql

from internals.db import Merchant as MerchantModel
from internals.enums import AvatarType

from ..enums import ApprovalStatusGQL
from .common import AvatarImageGQL

__all__ = ("MerchantGQL",)


@gql.type(name="Merchant", description="Merchant model")
class MerchantGQL:
    id: UUID = gql.field(description="The ID of the merchant")
    name: str = gql.field(description="The name of the merchant")
    description: str = gql.field(description="The description of the merchant")
    address: str = gql.field(description="The address of the merchant")
    created_at: datetime = gql.field(description="The creation time of the merchant")
    updated_at: datetime = gql.field(description="The last update time of the merchant")
    approved: ApprovalStatusGQL = gql.field(description="The approval status of the merchant")
    avatar: Optional[AvatarImageGQL] = gql.field(description="The avatar of the merchant")
    phone: Optional[str] = gql.field(description="The phone number of the merchant")
    email: Optional[str] = gql.field(description="The email of the merchant")
    website: Optional[str] = gql.field(description="The website of the merchant")

    @classmethod
    def from_db(cls: Type[MerchantGQL], merch: MerchantModel):
        avatar = None  # type: Optional[AvatarImageGQL]
        if merch.avatar and merch.avatar.key:
            avatar = AvatarImageGQL.from_db(merch.avatar, AvatarType.MERCHANT)
        return cls(
            id=merch.merchant_id,
            name=merch.name,
            description=merch.description,
            address=merch.address,
            created_at=merch.created_at,
            updated_at=merch.updated_at,
            approved=merch.approved,
            avatar=avatar,
            phone=merch.phone,
            email=merch.email,
            website=merch.website,
        )
