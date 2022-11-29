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
from dataclasses import dataclass

from datetime import datetime
from typing import Optional, Type
from uuid import UUID

import strawberry as gql
from bson import ObjectId

from internals.db import FoodItem as FoodItemModel
from internals.db import FoodOrder as FoodOrderModel
from internals.db import Merchant as MerchantModel
from internals.db import PaymentReceipt
from internals.db import User as UserModel

from ..enums import OrderStatusGQL
from .items import FoodItemGQL
from .merchant import MerchantGQL
from .user import UserGQL

__all__ = (
    "FoodOrderGQL",
    "OrderReceiptGQL",
    "PaymentMethodGQL",
    "FoodOrderItemInputGQL",
)


@dataclass
class PrivateItem:
    item_id: str
    quantity: int


@gql.type(name="OrderReceipt", description="The payment receipt of an order")
class OrderReceiptGQL:
    id: UUID = gql.field(description="The ID of the receipt")
    method: str = gql.field(description="The payment method used")
    amount: float = gql.field(description="The amount paid")
    data: str = gql.field(description="The card/account information used to pay")

    @classmethod
    def from_db(cls: Type[OrderReceiptGQL], data: PaymentReceipt) -> OrderReceiptGQL:
        return cls(
            id=data.pay_id,
            method=data.method,
            amount=data.amount,
            data=data.data,
        )


@gql.type(name="FoodOrderItem", description="The each item in an order")
class FoodOrderItemGQL:
    item_id: gql.Private[str]  # ObjectId(s)
    quantity: int = gql.field(description="The quantity of the item")

    @gql.field(description="The item information itself")
    async def data(self) -> FoodItemGQL:
        # Resolve items
        item = await FoodItemModel.find_one(FoodItemModel.id == ObjectId(self.item_id))
        if item is None:
            raise Exception(f"Unable to find item in database: {self.item_id}")
        return FoodItemGQL.from_db(item)


@gql.type(name="FoodOrder", description="Food/Item order model")
class FoodOrderGQL:
    id: UUID = gql.field(description="The ID of the order")
    target_address: str = gql.field(description="The target address delivery of the order")
    created_at: datetime = gql.field(description="The creation time of the order")
    updated_at: datetime = gql.field(description="The last update time of the order")
    status: OrderStatusGQL = gql.field(description="The order status")
    receipt: OrderReceiptGQL = gql.field(description="The payment receipt of this order")

    items_temp: gql.Private[list[PrivateItem]]  # a list of ObjectId(s)
    merchant_id: gql.Private[str]
    user_id: gql.Private[str]

    @gql.field(description="The list of associated items for the order")
    async def items(self) -> list[FoodOrderItemGQL]:
        # Resolve items
        order_items = [FoodOrderItemGQL(item_id=it.item_id, quantity=it.quantity) for it in self.items_temp]
        return order_items

    @gql.field(description="The associated merchant for the order")
    async def merchant(self) -> Optional[MerchantGQL]:
        # Resolve merchant
        merchant = await MerchantModel.find_one(MerchantModel.id == ObjectId(self.merchant_id))
        return MerchantGQL.from_db(merchant) if merchant else None

    @gql.field(description="The associated user for the order")
    async def user(self) -> Optional[UserGQL]:
        # Resolve user
        user = await UserModel.find_one(UserModel.id == ObjectId(self.user_id))
        return UserGQL.from_db(user) if user else None

    @classmethod
    def from_db(cls: Type[FoodOrderGQL], data: FoodOrderModel) -> FoodOrderGQL:
        return cls(
            id=data.order_id,
            target_address=data.target_address,
            created_at=data.created_at,
            updated_at=data.updated_at,
            status=data.status,
            receipt=OrderReceiptGQL.from_db(data.receipt),
            items_temp=[PrivateItem(item_id=str(item.data.ref.id), quantity=item.quantity) for item in data.items],
            merchant_id=str(data.merchant.ref.id),
            user_id=str(data.user.ref.id),
        )


@gql.input(name="PaymentMethod", description="The payment method used to pay")
class PaymentMethodGQL:
    method: str = gql.field(description="The payment method used")
    data: str = gql.field(description="The card/account information used to pay")


@gql.input(name="FoodOrderInput", description="Food/Item order input information")
class FoodOrderItemInputGQL:
    id: gql.ID = gql.field(description="The ID of the item")
    quantity: int = gql.field(description="The quantity of the item (default: `1`)", default=1)
