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

from beanie import PydanticObjectId
from beanie.operators import NotIn
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends

from internals.db import FoodOrder
from internals.depends import PaginationParams, SortDirection, pagination_parameters
from internals.enums import OrderStatus
from internals.models import FoodOrderResponse
from internals.responses import PaginatedResponseType, PaginationInfo, ResponseType
from internals.session import UserSession, check_session
from internals.utils import to_uuid

__all__ = ("router",)
router = APIRouter(prefix="/order", tags=["Orders"])
logger = logging.getLogger("Routes.Orders")


@router.get(
    "/",
    summary="Get all orders of current user",
    response_model=PaginatedResponseType[FoodOrderResponse],
)
async def get_user_orders(
    page_params: PaginationParams = Depends(pagination_parameters(default_limit=10)),
    include_all: bool = False,
    session: UserSession = Depends(check_session),
):
    """
    Returns the current user orders.

    You can also include all orders by setting the `include_all` parameter to `true`.
    If not, it will not include any finished order/problematic order.
    """

    limit = page_params["limit"]
    cursor = page_params["cursor"]
    sort = page_params["sort"]

    act_limit = limit + 1
    direction = "-" if sort is SortDirection.DESCENDING else "+"
    cursor_id = None
    if cursor is not None:
        try:
            cursor_id = ObjectId(cursor)
        except (TypeError, InvalidId):
            return PaginatedResponseType(error="Invalid cursor", code=400, page_info=PaginationInfo(0, 0, 0)).to_orjson(
                400
            )

    items_args = [FoodOrder.user.ref.id == PydanticObjectId(session.user_db)]
    not_in_args = NotIn(
        FoodOrder.status,
        [
            OrderStatus.CANCELED_MERCHANT,
            OrderStatus.CANCELLED,
            OrderStatus.PROBLEM_MERCHANT,
            OrderStatus.PROBLEM_FAIL_TO_DELIVER,
            OrderStatus.DONE,
        ],
    )
    if not include_all:
        items_args.append(not_in_args)
    if cursor_id is not None:
        items_args.append(FoodOrder.id >= cursor_id)

    items_associated = (
        await FoodOrder.find(*items_args, fetch_links=True).sort(f"{direction}_id").limit(act_limit).to_list()
    )
    if len(items_associated) < 1:
        return PaginatedResponseType[FoodOrderResponse](
            data=[],
            code=404,
            page_info=PaginationInfo(
                total=0,
                count=0,
                next_cursor=None,
                per_page=limit,
            ),
        ).to_orjson(404)
    items_associated_count = await FoodOrder.find(*items_args[:-1]).count()
    last_item = None
    if len(items_associated) > limit:
        last_item = items_associated.pop()

    mapped_items = [FoodOrderResponse.from_db(item) for item in items_associated]
    return PaginatedResponseType[FoodOrderResponse](
        data=mapped_items,
        page_info=PaginationInfo(
            total=items_associated_count,
            count=len(mapped_items),
            next_cursor=str(last_item.id) if last_item is not None else None,
            per_page=limit,
        ),
    ).to_orjson()


@router.get(
    "/{id}",
    summary="Get order info of specified ID",
    response_model=PaginatedResponseType[FoodOrderResponse],
)
async def get_order_info(
    id: str,
    session: UserSession = Depends(check_session),
):
    """
    Returns the order info of specified ID.
    """

    order = await FoodOrder.find_one(
        FoodOrder.order_id == to_uuid(id), FoodOrder.user.ref.id == PydanticObjectId(session.user_db), fetch_links=True
    )

    if order is None:
        return ResponseType(error="Order not found or not associated with your account", code=404).to_orjson(404)

    return ResponseType[FoodOrderResponse](data=FoodOrderResponse.from_db(order)).to_orjson()
