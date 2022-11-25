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

from dataclasses import dataclass, field
from typing import Optional

from pendulum.datetime import DateTime

from internals.db import Merchant as MerchantDB
from internals.enums import AvatarType

from .common import AvatarResponse, PartialIDName, _coerce_to_pendulum, pendulum_utc

__all__ = ("MerchantResponse",)


@dataclass
class MerchantResponse(PartialIDName):
    description: str
    address: str

    created_at: DateTime = field(default_factory=pendulum_utc)
    updated_at: DateTime = field(default_factory=pendulum_utc)

    # Optional stuff
    avatar: Optional[AvatarResponse] = field(default=None)
    phone: Optional[str] = field(default=None)
    email: Optional[str] = field(default=None)
    website: Optional[str] = field(default=None)

    def __post_init__(self):
        cc_at = _coerce_to_pendulum(self.created_at)
        cc_ut = _coerce_to_pendulum(self.updated_at)
        if cc_at is not None:
            self.created_at = cc_at
        if cc_ut is not None:
            self.updated_at = cc_ut

    @classmethod
    def from_db(cls, merchant: MerchantDB):
        avatar = None
        if merchant.avatar and merchant.avatar.key:
            avatar = AvatarResponse.from_db(merchant.avatar, AvatarType.ITEMS)
        return cls(
            id=str(merchant.merchant_id),
            name=merchant.name,
            description=merchant.description,
            address=merchant.address,
            avatar=avatar,
            phone=merchant.phone,
            email=merchant.email,
            website=merchant.website,
            created_at=merchant.created_at,
            updated_at=merchant.updated_at,
        )
