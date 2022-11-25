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
from bson import ObjectId

from internals.db import FoodItem as FoodItemModel
from internals.db import Merchant as MerchantModel
from internals.enums import AvatarType

from ..enums import ItemTypeGQL
from .common import AvatarImageGQL
from .merchant import MerchantGQL

__all__ = ("FoodItemGQL",)


@gql.type(name="FoodItem", description="Food/Item model")
class FoodItemGQL:
    id: UUID = gql.field(description="The ID of the item")
    name: str = gql.field(description="The name of the item")
    description: str = gql.field(description="The description of the item")
    price: float = gql.field(description="The price of the item")
    stock: int = gql.field(description="The stock of the item")
    type: ItemTypeGQL = gql.field(description="The item type")  # type: ignore
    created_at: datetime = gql.field(description="The creation time of the item")
    updated_at: datetime = gql.field(description="The last update time of the item")
    image: Optional[AvatarImageGQL] = gql.field(description="The image of the item")

    merchant_id: gql.Private[Optional[str]]

    @gql.field(description="The associated merchant for the item")
    async def merchant(self) -> Optional[MerchantGQL]:
        # Resolve merchant
        if self.merchant_id is None:
            return None
        merchant = await MerchantModel.find_one(MerchantModel.id == ObjectId(self.merchant_id))
        if merchant is None:
            return None
        return MerchantGQL.from_db(merchant)

    @classmethod
    def from_db(cls, data: FoodItemModel):
        avatar = None  # type: Optional[AvatarImageGQL]
        if data.avatar and data.avatar.key:
            avatar = AvatarImageGQL.from_db(data.avatar, AvatarType.ITEMS)
        merchant_id = None  # type: Optional[str]
        if data.merchant is not None:
            merchant_id = str(data.merchant.ref.id)
        return cls(
            id=data.item_id,
            name=data.name,
            description=data.description,
            price=data.price,
            stock=data.stock,
            type=data.type,
            created_at=data.created_at,
            updated_at=data.updated_at,
            image=avatar,
            merchant_id=merchant_id,
        )
