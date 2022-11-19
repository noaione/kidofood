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
from typing import TypedDict
from uuid import UUID

from bson import ObjectId
from pydantic import BaseModel

from internals.db import AvatarImage

from .common import AvatarResponse

__all__ = (
    "MerchantSearch",
    "FoodItemSearch",
    "ProjectionMerchant",
    "ProjectionFoodItem",
    "MultiSearchResponse",
)


@dataclass
class MerchantSearch:
    id: str
    name: str
    avatar: AvatarResponse


class ProjectionMerchant(BaseModel):
    id: ObjectId
    merchant_id: UUID
    name: str
    avatar: AvatarImage

    def to_response(self) -> MerchantSearch:
        return MerchantSearch(
            id=str(self.merchant_id),
            name=self.name,
            avatar=AvatarResponse.from_db(self.avatar, "merchant"),
        )

    class Config:
        arbitrary_types_allowed = True


@dataclass
class FoodItemSearch:
    id: str
    name: str
    description: str
    price: float
    avatar: AvatarResponse


class ProjectionFoodItem(BaseModel):
    id: ObjectId
    item_id: UUID
    name: str
    description: str
    price: float
    avatar: AvatarImage

    def to_response(self) -> FoodItemSearch:
        return FoodItemSearch(
            id=str(self.item_id),
            name=self.name,
            description=self.description,
            price=self.price,
            avatar=AvatarResponse.from_db(self.avatar, "items"),
        )

    class Config:
        arbitrary_types_allowed = True


class MultiSearchResponse(TypedDict):
    merchants: list[MerchantSearch]
    items: list[FoodItemSearch]
