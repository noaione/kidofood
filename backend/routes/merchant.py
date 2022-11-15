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

from fastapi import APIRouter, Depends

from internals.db import FoodItem, Merchant, UserType
from internals.models import FoodItemResponse, MerchantResponse
from internals.responses import ResponseType
from internals.session import UserSession, check_session_cookie, get_session_verifier
from internals.utils import to_uuid

__all__ = ("router",)
router = APIRouter(prefix="/merchant", tags=["Merchant"])
logger = logging.getLogger("Routes.Merchant")


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
async def merchant_get_items(id: str):
    """
    Returns a merchant's items by ID.
    """

    merchant = await Merchant.find_one(Merchant.merchant_id == to_uuid(id))
    if merchant is None:
        return ResponseType[list[FoodItemResponse]](error="Merchant not found", code=404).to_orjson(404)

    items_associated = await FoodItem.find(FoodItem.merchant.ref.id == merchant.id).to_list()
    mapped_items = list(map(FoodItemResponse.from_db, items_associated))

    return ResponseType[list[FoodItemResponse]](data=mapped_items).to_orjson()
