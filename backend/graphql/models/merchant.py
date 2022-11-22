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
from typing import Optional
from uuid import UUID

import strawberry as gql

from internals.db import Merchant as MerchantModel

from .common import AvatarImage, AvatarType

__all__ = ("Merchant",)


@gql.type
class Merchant:
    id: UUID
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    avatar: Optional[AvatarImage]
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]

    @classmethod
    def from_db(cls, merch: MerchantModel):
        avatar = None  # type: Optional[AvatarImage]
        if merch.avatar and merch.avatar.key:
            avatar = AvatarImage.from_db(merch.avatar, AvatarType.MERCHANT)
        return cls(
            id=merch.merchant_id,
            name=merch.name,
            description=merch.description,
            created_at=merch.created_at,
            updated_at=merch.updated_at,
            avatar=avatar,
            phone=merch.phone,
            email=merch.email,
            website=merch.website,
        )
