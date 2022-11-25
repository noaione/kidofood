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
from beanie.operators import In as OpIn
from bson import ObjectId

from internals.db import FoodItem as FoodItemModel
from internals.db import FoodOrder as FoodOrderModel
from internals.db import Merchant as MerchantModel
from internals.db import User as UserModel
from internals.enums import OrderStatus

from .items import FoodItem
from .merchant import Merchant
from .user import User

__all__ = ("FoodOrder",)


@gql.type
class FoodOrder:
    id: UUID = gql.field(description="The ID of the order")
    total: float = gql.field(description="The total price of the order")
    target_address: str = gql.field(description="The target address delivery of the order")
    created_at: datetime = gql.field(description="The creation time of the order")
    updated_at: datetime = gql.field(description="The last update time of the order")
    status: gql.enum(OrderStatus, description="The order status")  # type: ignore

    item_ids: gql.Private[list[str]]  # a list of ObjectId(s)
    merchant_id: gql.Private[str]
    user_id: gql.Private[str]

    @gql.field(description="The list of associated items for the order")
    async def items(self) -> list[FoodItem]:
        # Resolve items
        object_ids = [ObjectId(item_id) for item_id in self.item_ids]
        items = await FoodItemModel.find(OpIn(FoodItemModel.id, object_ids)).to_list()
        return [FoodItem.from_db(item) for item in items]

    @gql.field(description="The associated merchant for the order")
    async def merchant(self) -> Optional[Merchant]:
        # Resolve merchant
        merchant = await MerchantModel.find_one(MerchantModel.id == ObjectId(self.merchant_id))
        return Merchant.from_db(merchant) if merchant else None

    @gql.field(description="The associated user for the order")
    async def user(self) -> Optional[User]:
        # Resolve user
        user = await UserModel.find_one(UserModel.id == ObjectId(self.user_id))
        return User.from_db(user) if user else None

    @classmethod
    def from_db(cls, data: FoodOrderModel) -> FoodOrder:
        return cls(
            id=data.order_id,
            total=data.total,
            target_address=data.target_address,
            created_at=data.created_at,
            updated_at=data.updated_at,
            status=data.status,
            item_ids=[str(item_id.ref.id) for item_id in data.items],
            merchant_id=str(data.merchant.ref.id),
            user_id=str(data.user.ref.id),
        )
