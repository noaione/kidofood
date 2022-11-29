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
from uuid import UUID, uuid4

from beanie import Document, Link, Replace, SaveChanges, Update, after_event, before_event
from pendulum.datetime import DateTime
from pydantic import BaseModel, Field

from internals.enums import ApprovalStatus, ItemType, OrderStatus, UserType
from internals.pubsub import get_pubsub

from ._doc import _coerce_to_pendulum, pendulum_utc

__all__ = (
    "AvatarImage",
    "Merchant",
    "FoodItem",
    "User",
    "FoodOrder",
    "PaymentReceipt",
)


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
    approved: ApprovalStatus = ApprovalStatus.PENDING

    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]

    created_at: DateTime = Field(default_factory=pendulum_utc)
    updated_at: DateTime = Field(default_factory=pendulum_utc)

    class Settings:
        name = "FoodMerchants"
        use_state_management = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _coerce_to_pendulum(self)

    @before_event(Replace, Update, SaveChanges)
    def update_time(self):
        self.updated_at = pendulum_utc()


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

    created_at: DateTime = Field(default_factory=pendulum_utc)
    updated_at: DateTime = Field(default_factory=pendulum_utc)

    class Settings:
        name = "FoodItems"
        use_state_management = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _coerce_to_pendulum(self)

    @before_event(Replace, Update, SaveChanges)
    def update_time(self):
        self.updated_at = pendulum_utc()


class PaymentReceipt(BaseModel):
    pay_id: UUID = Field(default_factory=uuid4, unique=True)
    method: str
    amount: float
    data: str  # Let's just use normal string for account mail card number, or something for now


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

    created_at: DateTime = Field(default_factory=pendulum_utc)
    updated_at: DateTime = Field(default_factory=pendulum_utc)

    class Settings:
        name = "Users"
        use_state_management = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _coerce_to_pendulum(self)

    @before_event(Replace, Update, SaveChanges)
    def update_time(self):
        self.updated_at = pendulum_utc()


class FoodOrderItem(BaseModel):
    data: Link[FoodItem]
    quantity: int = 1


class FoodOrder(Document):
    order_id: UUID = Field(default_factory=uuid4, unique=True)
    items: list[FoodOrderItem]
    user: Link[User]
    rider: Optional[Link[User]]
    merchant: Link[Merchant]
    status: OrderStatus = OrderStatus.PENDING
    target_address: str
    receipt: PaymentReceipt

    created_at: DateTime = Field(default_factory=pendulum_utc)
    updated_at: DateTime = Field(default_factory=pendulum_utc)

    class Config:
        collection = "FoodOrders"
        use_state_management = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _coerce_to_pendulum(self)

    @before_event(Replace, Update, SaveChanges)
    def update_time(self):
        self.updated_at = pendulum_utc()

    @after_event(Replace, Update, SaveChanges)
    def publish_changes(self):
        ps = get_pubsub()
        ps.publish(f"order:updated:{str(self.order_id)}", self)
