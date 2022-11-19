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
from functools import partial as ftpartial
from typing import Optional
from uuid import UUID, uuid4

import pendulum
from beanie import Document, Link
from pydantic import BaseModel, Field

from ._doc import _coerce_to_pendulum

__all__ = (
    "ItemType",
    "UserType",
    "OrderStatus",
    "AvatarImage",
    "Merchant",
    "FoodItem",
    "User",
    "FoodOrder",
)
pendulum_utc = ftpartial(pendulum.now, tz="UTC")


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


class AvatarImage(BaseModel):
    key: str = ""
    format: str = ""


class Merchant(Document):
    merchant_id: UUID = Field(default_factory=uuid4, unique=True)
    name: str
    description: str
    address: str

    # S3 key
    avatar: AvatarImage = Field(default_factory=AvatarImage)

    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]

    created_at: pendulum.DateTime = Field(default_factory=pendulum_utc)
    updated_at: pendulum.DateTime = Field(default_factory=pendulum_utc)

    class Settings:
        name = "FoodMerchants"
        use_state_management = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _coerce_to_pendulum(self)


class FoodItem(Document):
    item_id: UUID = Field(default_factory=uuid4, unique=True)
    name: str
    description: str
    stock: int
    price: float
    type: ItemType
    # S3 key
    avatar: AvatarImage = Field(default_factory=AvatarImage)

    merchant: Link[Merchant]

    created_at: pendulum.DateTime = Field(default_factory=pendulum_utc)
    updated_at: pendulum.DateTime = Field(default_factory=pendulum_utc)

    class Settings:
        name = "FoodItems"
        use_state_management = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _coerce_to_pendulum(self)


class User(Document):
    user_id: UUID = Field(default_factory=uuid4, unique=True)
    name: str
    email: str = Field(unique=True)
    # Hashed password (scrypt)
    password: str
    type: UserType = UserType.CUSTOMER
    # Multiple addresses
    address: list[str] = Field(default_factory=list)
    # S3 key
    avatar: AvatarImage = Field(default_factory=AvatarImage)

    # merchant association if type is merchant
    merchant: Optional[Link[Merchant]] = Field(default=None)

    created_at: pendulum.DateTime = Field(default_factory=pendulum_utc)
    updated_at: pendulum.DateTime = Field(default_factory=pendulum_utc)

    class Settings:
        name = "Users"
        use_state_management = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _coerce_to_pendulum(self)


class FoodOrder(Document):
    order_id: UUID = Field(default_factory=uuid4, unique=True)
    items: list[Link[FoodItem]]
    total: float
    user: Link[User]
    merchant: Link[Merchant]
    status: OrderStatus = OrderStatus.PENDING
    target_address: str

    created_at: pendulum.DateTime = Field(default_factory=pendulum_utc)
    updated_at: pendulum.DateTime = Field(default_factory=pendulum_utc)

    class Config:
        collection = "FoodOrders"
        use_state_management = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _coerce_to_pendulum(self)
