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
from functools import partial as ftpartial

from beanie.operators import RegEx
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends

from internals.db import FoodItem, Merchant
from internals.depends import DualPaginationParams, PaginationParams, SortDirection, pagination_parameters
from internals.models import (
    FoodItemSearch,
    MerchantSearch,
    MultiSearchResponse,
    ProjectionFoodItem,
    ProjectionMerchant,
)
from internals.responses import PaginatedMultiResponseType, PaginatedResponseType, PaginationInfo

__all__ = ("router",)
router = APIRouter(prefix="/search", tags=["Search"])
logger = logging.getLogger("Routes.Search")


@router.get(
    "/", summary="Global search merchant + items", response_model=PaginatedMultiResponseType[MultiSearchResponse]
)
async def search_get(
    query: str,
    page_params: DualPaginationParams = Depends(
        pagination_parameters(max_limit=250, default_limit=10, dual_cursor=True)
    ),
):
    """
    Search for merchants and food items.
    """
    SearchRe = ftpartial(RegEx, pattern=query, options="i")

    limit = page_params["limit"]
    cursor_a = page_params["cursor_a"]
    cursor_b = page_params["cursor_b"]
    sort = page_params["sort"]

    act_limit = limit + 1
    direction = "-" if sort is SortDirection.DESCENDING else "+"
    merch_args = [SearchRe(Merchant.name)]
    items_args = [SearchRe(FoodItem.name)]
    if cursor_a is not None:
        try:
            cursor_id_a = ObjectId(cursor_a)
        except (TypeError, InvalidId):
            return PaginatedMultiResponseType(error="Invalid cursor_a", code=400).to_orjson(400)
        merch_args.append(Merchant.id >= cursor_id_a)  # type: ignore
    if cursor_b is not None:
        try:
            cursor_id_b = ObjectId(cursor_b)
        except (TypeError, InvalidId):
            return PaginatedMultiResponseType(error="Invalid cursor_b", code=400).to_orjson(400)
        items_args.append(FoodItem.id >= cursor_id_b)  # type: ignore

    merchants = (
        await Merchant.find(*merch_args).sort(f"{direction}_id").limit(act_limit).project(ProjectionMerchant).to_list()
    )
    food_items = (
        await FoodItem.find(*items_args).sort(f"{direction}_id").limit(act_limit).project(ProjectionFoodItem).to_list()
    )
    if len(merchants) < 1 and len(food_items) < 1:
        return PaginatedMultiResponseType(
            code=404,
            data={"merchants": [], "items": []},
            page_info={
                "merchants": PaginationInfo(
                    total=0,
                    count=0,
                    next_cursor=None,
                    per_page=limit,
                ),
                "items": PaginationInfo(
                    total=0,
                    count=0,
                    next_cursor=None,
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
                next_cursor=str(last_item_merchant.id) if last_item_merchant is not None else None,
                per_page=limit,
            ),
            "items": PaginationInfo(
                total=food_items_count,
                count=int(len(coerced_items)),
                next_cursor=str(last_item_item.id) if last_item_item is not None else None,
                per_page=limit,
            ),
        },
    ).to_orjson()


@router.get("/merchants", summary="Search for merchants", response_model=PaginatedResponseType[MerchantSearch])
async def search_merchants_get(
    query: str,
    page_params: PaginationParams = Depends(pagination_parameters(default_limit=10)),
):
    """
    Search for merchants.
    """
    limit = page_params["limit"]
    cursor = page_params["cursor"]
    sort = page_params["sort"]

    act_limit = limit + 1
    direction = "-" if sort is SortDirection.DESCENDING else "+"
    args = [RegEx(Merchant.name, pattern=query, options="i")]
    if cursor is not None:
        try:
            cursor_id = ObjectId(cursor)
        except (TypeError, InvalidId):
            return PaginatedResponseType(error="Invalid cursor", code=400, page_info=PaginationInfo(0, 0, 0)).to_orjson(
                400
            )
        args.append(Merchant.id >= cursor_id)  # type: ignore

    merchants = (
        await Merchant.find(*args).sort(f"{direction}_id").limit(act_limit).project(ProjectionMerchant).to_list()
    )
    if len(merchants) < 1:
        return PaginatedResponseType[MerchantSearch](
            data=[],
            code=404,
            page_info=PaginationInfo(
                total=0,
                count=0,
                next_cursor=None,
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
            next_cursor=str(last_item.id) if last_item is not None else None,
            per_page=limit,
        ),
    ).to_orjson()


@router.get("/items", summary="Search for items", response_model=PaginatedResponseType[FoodItemSearch])
async def search_items_get(
    query: str,
    page_params: PaginationParams = Depends(pagination_parameters(default_limit=10)),
):
    """
    Search for food items.
    """
    limit = page_params["limit"]
    cursor = page_params["cursor"]
    sort = page_params["sort"]

    act_limit = limit + 1
    direction = "-" if sort is SortDirection.DESCENDING else "+"
    args = [RegEx(FoodItem.name, pattern=query, options="i")]
    if cursor is not None:
        try:
            cursor_id = ObjectId(cursor)
        except (TypeError, InvalidId):
            return PaginatedResponseType(error="Invalid cursor", code=400, page_info=PaginationInfo(0, 0, 0)).to_orjson(
                400
            )
        args.append(FoodItem.id >= cursor_id)  # type: ignore

    food_items = (
        await FoodItem.find(*args).sort(f"{direction}_id").limit(act_limit).project(ProjectionFoodItem).to_list()
    )
    if len(food_items) < 1:
        return PaginatedResponseType[FoodItemSearch](
            data=[],
            code=404,
            page_info=PaginationInfo(
                total=0,
                count=0,
                next_cursor=None,
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
            next_cursor=str(last_item.id) if last_item is not None else None,
            per_page=limit,
        ),
    ).to_orjson()
