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
from typing import Optional, Type

from pendulum.datetime import DateTime

from internals.db import FoodItem as FoodItemDB
from internals.db import FoodOrder as FoodOrderDB
from internals.db import Merchant as MerchantDB
from internals.db import PaymentReceipt as PaymentReceiptDB
from internals.db import User as UserDB
from internals.enums import AvatarType, OrderStatus

from .common import AvatarResponse, PartialID, PartialIDAvatar, _coerce_to_pendulum, pendulum_utc
from .items import FoodItemResponse

__all__ = ("FoodOrderResponse",)


@dataclass
class OrderReceiptResponse(PartialID):
    method: str
    amount: float
    data: str

    @classmethod
    def from_db(
        cls: Type[OrderReceiptResponse],
        db: PaymentReceiptDB,
    ) -> OrderReceiptResponse:
        return cls(
            id=str(db.pay_id),
            method=db.method,
            amount=db.amount,
            data=db.data,
        )


@dataclass
class FoodOrderResponse(PartialID):
    items: list[FoodItemResponse]
    receipt: OrderReceiptResponse

    # user/merchant
    user: PartialIDAvatar
    merchant: PartialIDAvatar

    target_address: str
    created_at: DateTime = field(default_factory=pendulum_utc)
    updated_at: DateTime = field(default_factory=pendulum_utc)

    status: OrderStatus = OrderStatus.PENDING

    def __post_init__(self):
        cc_at = _coerce_to_pendulum(self.created_at)
        cc_ut = _coerce_to_pendulum(self.updated_at)
        if cc_at is not None:
            self.created_at = cc_at
        if cc_ut is not None:
            self.updated_at = cc_ut

    @classmethod
    def from_db(
        cls: Type[FoodOrderResponse],
        db: FoodOrderDB,
        user_info: Optional[PartialIDAvatar] = None,
        merchant_info: Optional[PartialIDAvatar] = None,
    ) -> FoodOrderResponse:
        merchant = db.merchant if isinstance(db.merchant, MerchantDB) else merchant_info
        if merchant is None:
            raise ValueError("Merchant info is required, either passing the prefetched DB or passing the merchant info")
        user = db.user if isinstance(db.user, UserDB) else user_info
        if user is None:
            raise ValueError("User info is required, either passing the prefetched DB or passing the user info")
        prefetched_items: list[FoodItemResponse] = []
        for idx, item in enumerate(db.items):
            if not isinstance(item, FoodItemDB):
                raise TypeError(
                    f"items[{idx}] is not a FoodItem, got {type(item)} instead, make sure to prefetch the Link!"
                )
            prefetched_items.append(FoodItemResponse.from_db(item, merchant_info))
        if isinstance(merchant, MerchantDB):
            merchant = PartialIDAvatar(
                str(merchant.merchant_id),
                merchant.name,
                AvatarResponse.from_db(merchant.avatar, AvatarType.MERCHANT),
            )
        if isinstance(user, UserDB):
            user = PartialIDAvatar(
                str(user.user_id),
                user.name,
                AvatarResponse.from_db(user.avatar, AvatarType.USERS),
            )
        return cls(
            id=str(db.order_id),
            items=prefetched_items,
            receipt=OrderReceiptResponse.from_db(db.receipt),
            user=user,
            merchant=merchant,
            target_address=db.target_address,
            created_at=db.created_at,
            updated_at=db.updated_at,
            status=db.status,
        )
