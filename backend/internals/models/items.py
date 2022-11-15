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
from datetime import datetime
from typing import Optional

import pendulum

from internals.db import FoodItem as FoodItemDB
from internals.db import ItemType

from .common import AvatarResponse, pendulum_utc

__all__ = ("FoodItemResponse",)


@dataclass
class FoodItemResponse:
    id: str
    name: str
    description: str
    price: float
    stock: int
    type: ItemType
    image: Optional[AvatarResponse] = None
    created_at: pendulum.DateTime = field(default_factory=pendulum_utc)
    updated_at: pendulum.DateTime = field(default_factory=pendulum_utc)

    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = pendulum.parse(self.created_at)
        if isinstance(self.updated_at, str):
            self.updated_at = pendulum.parse(self.updated_at)
        if isinstance(self.created_at, int):
            self.created_at = pendulum.from_timestamp(self.created_at)
        if isinstance(self.updated_at, int):
            self.updated_at = pendulum.from_timestamp(self.updated_at)
        if isinstance(self.created_at, datetime):
            self.created_at = pendulum.instance(self.created_at)
        if isinstance(self.updated_at, datetime):
            self.updated_at = pendulum.instance(self.updated_at)

    @classmethod
    def from_db(cls, db: FoodItemDB) -> FoodItemResponse:
        avatar = None
        if db.avatar and db.avatar.key:
            avatar = AvatarResponse.from_db(db.avatar, "items")
        return cls(
            id=str(db.item_id),
            name=db.name,
            description=db.description,
            price=db.price,
            availability=db.stock,
            type=db.type,
            image=avatar,
            created_at=db.created_at,
            updated_at=db.updated_at,
        )
