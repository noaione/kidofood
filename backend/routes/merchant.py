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
from typing import Literal, Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends

from internals.db import FoodItem, Merchant, UserType
from internals.models import FoodItemResponse, MerchantResponse
from internals.responses import PaginatedResponseType, PaginationInfo, ResponseType
from internals.session import UserSession, check_session_cookie, get_session_verifier
from internals.utils import to_uuid

__all__ = ("router",)
router = APIRouter(prefix="/merchant", tags=["Merchant"])
logger = logging.getLogger("Routes.Merchant")
SortDirection = Literal["asc", "ascending", "desc", "descending"]


@router.get(
    "/merchants",
    summary="Get all merchants (Admin)",
    response_model=ResponseType[list[MerchantResponse]],
    dependencies=[Depends(check_session_cookie)],
)
async def merchants_get(session: UserSession = Depends(get_session_verifier)):
    """
    Returns all merchants registered with KidoFood.
    """

    if session.type != UserType.ADMIN:
        return ResponseType[list[MerchantResponse]](
            error="You are not authorized to access this information", code=403, data=[]
        ).to_orjson(403)

    merchants = await Merchant.find_all().to_list()
    mapped_merchants = list(map(MerchantResponse.from_db, merchants))

    return ResponseType[list[MerchantResponse]](data=mapped_merchants).to_orjson()


@router.get(
    "/merchant",
    summary="Get (your) merchant information",
    response_model=ResponseType[MerchantResponse],
)
async def merchant_get(session: UserSession = Depends(get_session_verifier)):
    """
    Returns merchant information of the user.
    """

    if session.type == UserType.CUSTOMER:
        return ResponseType[MerchantResponse](
            error="You are not authorized to access this information", code=403, data=None
        ).to_orjson(403)

    if session.type == UserType.ADMIN:
        return ResponseType[MerchantResponse](error="Please use the /merchants route", code=403, data=None).to_orjson(
            403
        )

    if session.merchant_info is None:
        return ResponseType[MerchantResponse](
            error="You don't have any merchant account associated", code=404, data=None
        ).to_orjson(404)

    merchant_info = await session.merchant_info.fetch()
    if not isinstance(merchant_info, Merchant):
        return ResponseType[MerchantResponse](error="Merchant information is not valid", code=404, data=None).to_orjson(
            404
        )

    return ResponseType[MerchantResponse](data=MerchantResponse.from_db(merchant_info)).to_orjson()


@router.get(
    "/merchant/{id}",
    summary="Get merchant by ID",
    response_model=ResponseType[MerchantResponse],
)
async def merchant_get_single(id: str):
    """
    Returns a merchant by ID.
    """

    merchant = await Merchant.find_one(Merchant.merchant_id == to_uuid(id))
    if merchant is None:
        return ResponseType[MerchantResponse](error="Merchant not found", code=404).to_orjson(404)

    return ResponseType[MerchantResponse](data=MerchantResponse.from_db(merchant)).to_orjson()


@router.get(
    "/merchant/{id}/items",
    summary="Get merchant items by ID",
    response_model=ResponseType[list[FoodItemResponse]],
)
async def merchant_get_items(
    id: str,
    limit: int = 20,
    cursor: Optional[str] = None,
    sort: SortDirection = "asc",
):
    """
    Returns a merchant's items by ID.
    """

    act_limit = limit + 1
    direction = "-" if sort.lower().startswith("desc") else "+"
    cursor_id = None
    if cursor is not None:
        try:
            cursor_id = ObjectId(cursor)
        except (TypeError, InvalidId):
            return PaginatedResponseType(error="Invalid cursor", code=400).to_orjson(400)

    merchant = await Merchant.find_one(Merchant.merchant_id == to_uuid(id))
    if merchant is None:
        return PaginatedResponseType[FoodItemResponse](error="Merchant not found", code=404).to_orjson(404)

    items_args = [FoodItem.merchant.ref.id == merchant.id]
    if cursor_id is not None:
        items_args.append(FoodItem.id >= cursor_id)

    items_associated = await FoodItem.find(*items_args).sort(f"{direction}_id").limit(act_limit).to_list()
    if len(items_associated) < 1:
        return PaginatedResponseType[FoodItemResponse](
            data=[],
            code=404,
            page_info=PaginationInfo(
                total=0,
                count=0,
                cursor=None,
                per_page=limit,
            ),
        ).to_orjson(404)
    items_associated_count = await FoodItem.find(FoodItem.merchant.ref.id == merchant.id).count()

    last_item = None
    if len(items_associated) > limit:
        last_item = items_associated.pop()
    mapped_items = list(map(FoodItemResponse.from_db, items_associated))

    return PaginatedResponseType[FoodItemResponse](
        data=mapped_items,
        page_info=PaginationInfo(
            total=items_associated_count,
            count=len(mapped_items),
            cursor=str(last_item.id) if last_item is not None else None,
            per_page=limit,
        ),
    ).to_orjson()
