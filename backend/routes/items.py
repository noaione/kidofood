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

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends

from internals.db import FoodItem
from internals.depends import PaginationParams, SortDirection, pagination_parameters
from internals.models import FoodItemResponse
from internals.responses import PaginatedResponseType, PaginationInfo, ResponseType
from internals.utils import to_uuid

__all__ = ("router",)
router = APIRouter(prefix="/items", tags=["Items"])
logger = logging.getLogger("Routes.Items")


@router.get(
    "/",
    summary="Get all items (paginated)",
    response_model=PaginatedResponseType[FoodItemResponse],
)
async def get_all_items(
    page_params: PaginationParams = Depends(pagination_parameters(max_limit=250, default_limit=10)),
):
    """
    Get all items available in KidoFood, use pagination.
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
            return PaginatedResponseType(error="Invalid cursor", code=400).to_orjson(400)

    items_args = []
    if cursor_id is not None:
        items_args.append(FoodItem.id >= cursor_id)

    items_associated = (
        await FoodItem.find(*items_args, fetch_links=True).sort(f"{direction}_id").limit(act_limit).to_list()
    )
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
    items_associated_count = await FoodItem.find().count()

    last_item = None
    if len(items_associated) > limit:
        last_item = items_associated.pop()
    mapped_items = [FoodItemResponse.from_db(item) for item in items_associated]

    return PaginatedResponseType[FoodItemResponse](
        data=mapped_items,
        page_info=PaginationInfo(
            total=items_associated_count,
            count=len(mapped_items),
            cursor=str(last_item.id) if last_item is not None else None,
            per_page=limit,
        ),
    ).to_orjson()


@router.get(
    "/{item_id}",
    summary="Get item by ID",
    response_model=ResponseType[FoodItemResponse],
)
async def get_item_by_id(item_id: str):
    """
    Get item by ID.
    """

    item_id = to_uuid(item_id)
    if item_id is None:
        return ResponseType(error="Invalid item ID", code=400).to_orjson(400)

    item = await FoodItem.find_one(FoodItem.id == item_id, fetch_links=True)
    if item is None:
        return ResponseType(error="Item not found", code=404).to_orjson(404)

    return ResponseType[FoodItemResponse](data=FoodItemResponse.from_db(item)).to_orjson()
