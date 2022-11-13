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

from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from bson import ObjectId
from odmantic import Field, Model, Reference, query

if TYPE_CHECKING:
    from odmantic import AIOEngine


def make_uuid():
    return str(uuid4())


class ItemType(str, Enum):
    DRINK = "drink"
    MEAL = "meal"
    PACKAGE = "package"


class UserType(int, Enum):
    CUSTOMER = 0
    MERCHANT = 1
    ADMIN = 999


class OrderStatus(int, Enum):
    # Pending payment
    PENDING = 0
    # Payment is done, submitted to merchant
    FORWARDED = 1
    # Merchant accepted the order, processing
    ACCEPTED = 2
    # Merchant processing the order
    PROCESSING = 3
    # Merchant finished processing the order, delivery
    DELIVERING = 4
    # Merchant rejected the order
    REJECTED = 100
    # User cancelled the order
    CANCELLED = 101
    # Merchant canceled the order
    CANCELED_MERCHANT = 102
    # Problem with the order
    # merchant problem
    PROBLEM_MERCHANT = 103
    # user problem
    PROBLEM_FAIL_TO_DELIVER = 104
    # Order is complete
    DONE = 200


class Merchant(Model):
    merchant_id: str = Field(default_factory=make_uuid)
    name: str
    description: str
    # S3 key
    logo: str
    address: str
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]

    class Config:
        collection = "FoodMerchants"


class FoodItem(Model):
    item_id: str = Field(default_factory=make_uuid)
    name: str = Field(index=True)
    stock: int
    price: float
    type: ItemType = Field(index=True)

    merchant: Merchant = Reference()

    class Config:
        collection = "FoodItems"


class User(Model):
    user_id: str = Field(default_factory=make_uuid)
    name: str
    email: str = Field(index=True, unique=True)
    # Hashed password (scrypt)
    password: str
    type: UserType = Field(index=True)
    # Multiple addresses
    address: list[str] = Field(default_factory=list)

    merchant: Optional[Merchant] = Reference()

    class Config:
        collection = "Users"


class FoodOrder(Model):
    order_id: str = Field(default_factory=make_uuid)
    items: list[ObjectId]
    total: float
    user: User = Reference()
    status: OrderStatus = Field(index=True)
    target_address: str

    class Config:
        collection = "FoodOrders"

    async def get_items(self, engine: AIOEngine):
        food_item = await engine.find(FoodItem, query.in_(FoodItem.id, self.items))
        return food_item
