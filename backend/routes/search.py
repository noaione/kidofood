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

import logging
from dataclasses import dataclass
from functools import partial as ftpartial
from typing import Literal, Optional, TypedDict
from uuid import UUID

from beanie.operators import RegEx
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter
from pydantic import BaseModel

from internals.db import AvatarImage, FoodItem, Merchant
from internals.models import AvatarResponse
from internals.responses import PaginatedMultiResponseType, PaginatedResponseType, PaginationInfo

__all__ = ("router",)
router = APIRouter(prefix="/search", tags=["Search"])
logger = logging.getLogger("Routes.Search")
SortDirection = Literal["asc", "ascending", "desc", "descending"]


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
            id=self.merchant_id,
            name=self.name,
            avatar=AvatarResponse.from_db(self.avatar, "merchant"),
        )


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
            id=self.item_id,
            name=self.name,
            description=self.description,
            price=self.price,
            avatar=AvatarResponse.from_db(self.avatar, "items"),
        )


class MultiSearchResponse(TypedDict):
    merchants: list[MerchantSearch]
    items: list[FoodItemSearch]


@router.get(
    "/", summary="Global search merchant + items", response_model=PaginatedMultiResponseType[MultiSearchResponse]
)
async def search_get(
    query: str,
    limit: int = 10,
    cursor_a: Optional[str] = None,
    cursor_b: Optional[str] = None,
    sort: SortDirection = "asc",
):
    """
    Search for merchants and food items.
    """
    SearchRe = ftpartial(RegEx, pattern=query, options="i")

    act_limit = limit + 1
    direction = "-" if sort.lower().startswith("desc") else "+"
    merch_args = [SearchRe(Merchant.name)]
    items_args = [SearchRe(FoodItem.name)]
    if cursor_a is not None:
        try:
            cursor_id_a = ObjectId(cursor_a)
        except (TypeError, InvalidId):
            return PaginatedMultiResponseType(error="Invalid cursor_a", code=400).to_orjson(400)
        merch_args.append(Merchant.id >= cursor_id_a)
    if cursor_b is not None:
        try:
            cursor_id_b = ObjectId(cursor_b)
        except (TypeError, InvalidId):
            return PaginatedMultiResponseType(error="Invalid cursor_b", code=400).to_orjson(400)
        items_args.append(FoodItem.id >= cursor_id_b)

    merchants = (
        await Merchant.find(merch_args).sort(f"{direction}_id").limit(act_limit).project(ProjectionMerchant).to_list()
    )
    food_items = (
        await FoodItem.find(items_args).sort(f"{direction}_id").limit(act_limit).project(ProjectionFoodItem).to_list()
    )
    if len(merchants) < 1 and len(food_items) < 1:
        return PaginatedMultiResponseType(
            code=404,
            data={"merchants": [], "items": []},
            page_info={
                "merchants": PaginationInfo(
                    total=0,
                    count=0,
                    cursor=None,
                    per_page=limit,
                ),
                "items": PaginationInfo(
                    total=0,
                    count=0,
                    cursor=None,
                    per_page=limit,
                ),
            },
        ).to_orjson(404)
    merchant_count = 0
    food_items_count = 0
    if len(merchants) > 0:
        merchant_count = await Merchant.find(SearchRe(Merchant.name)).count()
    if len(food_items) > 0:
        food_items_count = await FoodItem.find(SearchRe(FoodItem.name)).count()

    last_item_merchant = None
    last_item_item = None
    if len(merchants) > limit:
        last_item_merchant = merchants.pop()
    if len(food_items) > limit:
        last_item_item = food_items.pop()

    coerced_merchant = [i.to_response() for i in merchants]
    coerced_items = [i.to_response() for i in food_items]

    return PaginatedMultiResponseType[MultiSearchResponse](
        data={
            "merchants": coerced_merchant,
            "items": coerced_items,
        },
        page_info={
            "merchants": PaginationInfo(
                total=merchant_count,
                count=int(len(coerced_merchant)),
                cursor=last_item_merchant.id if last_item_merchant is not None else None,
                per_page=limit,
            ),
            "items": PaginationInfo(
                total=food_items_count,
                count=int(len(coerced_items)),
                cursor=last_item_item.id if last_item_item is not None else None,
                per_page=limit,
            ),
        },
    ).to_orjson()


@router.get("/merchants", summary="Search for merchants", response_model=PaginatedResponseType[MerchantSearch])
async def search_merchants_get(
    query: str,
    limit: int = 10,
    cursor: Optional[str] = None,
    sort: SortDirection = "asc",
):
    """
    Search for merchants.
    """
    act_limit = limit + 1
    direction = "-" if sort.lower().startswith("desc") else "+"
    args = [RegEx(Merchant.name, pattern=query, options="i")]
    if cursor is not None:
        try:
            cursor_id = ObjectId(cursor)
        except (TypeError, InvalidId):
            return PaginatedMultiResponseType(error="Invalid cursor", code=400).to_orjson(400)
        args.append(Merchant.id >= cursor_id)

    merchants = await Merchant.find(args).sort(f"{direction}_id").limit(act_limit).project(ProjectionMerchant).to_list()
    if len(merchants) < 1:
        return PaginatedResponseType[MerchantSearch](
            data=[],
            code=404,
            page_info=PaginationInfo(
                total=0,
                count=0,
                cursor=None,
                per_page=limit,
            ),
        ).to_orjson(404)
    merchant_count = await Merchant.find(RegEx(Merchant.name, pattern=query, options="i")).count()

    last_item = None
    if len(merchants) > limit:
        last_item = merchants.pop()

    return PaginatedResponseType[MerchantSearch](
        data=[i.to_response() for i in merchants],
        page_info=PaginationInfo(
            total=merchant_count,
            count=int(len(merchants)),
            cursor=last_item.id if last_item is not None else None,
            per_page=limit,
        ),
    ).to_orjson()


@router.get("/items", summary="Search for items", response_model=PaginatedResponseType[FoodItemSearch])
async def search_items_get(
    query: str,
    limit: int = 10,
    cursor: Optional[str] = None,
    sort: SortDirection = "asc",
):
    """
    Search for food items.
    """
    act_limit = limit + 1
    direction = "-" if sort.lower().startswith("desc") else "+"
    args = [RegEx(FoodItem.name, pattern=query, options="i")]
    if cursor is not None:
        try:
            cursor_id = ObjectId(cursor)
        except (TypeError, InvalidId):
            return PaginatedMultiResponseType(error="Invalid cursor", code=400).to_orjson(400)
        args.append(FoodItem.id >= cursor_id)

    food_items = (
        await FoodItem.find(args).sort(f"{direction}_id").limit(act_limit).project(ProjectionFoodItem).to_list()
    )
    if len(food_items) < 1:
        return PaginatedResponseType[FoodItemSearch](
            data=[],
            code=404,
            page_info=PaginationInfo(
                total=0,
                count=0,
                cursor=None,
                per_page=limit,
            ),
        ).to_orjson(404)
    food_items_count = await FoodItem.find(RegEx(FoodItem.name, pattern=query, options="i")).count()

    last_item = None
    if len(food_items) > limit:
        last_item = food_items.pop()

    return PaginatedResponseType[FoodItemSearch](
        data=[i.to_response() for i in food_items],
        page_info=PaginationInfo(
            total=food_items_count,
            count=int(len(food_items)),
            cursor=last_item.id if last_item is not None else None,
            per_page=limit,
        ),
    ).to_orjson()
