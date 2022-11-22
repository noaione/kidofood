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

from enum import Enum
from typing import Optional, Union

import strawberry as gql
from beanie.operators import In as OpIn
from bson import ObjectId
from bson.errors import InvalidId

from internals.db import Merchant as MerchantDB

from .models import Connection, Merchant, PageInfo

__all__ = (
    "Cursor",
    "SortDirection",
    "resolve_merchant_paginated",
)
Cursor = str


class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"
    ASCENDING = "asc"
    DESCENDING = "desc"


def parse_cursor(cursor: Optional[Cursor]) -> Optional[ObjectId]:
    if cursor is None:
        return None
    if cursor is gql.UNSET:
        return None
    try:
        return ObjectId(cursor)
    except (TypeError, InvalidId):
        raise ValueError(f"Invalid cursor: {cursor}")


def to_cursor(obj_id: Optional[ObjectId]) -> Optional[Cursor]:
    return str(obj_id) if obj_id is not None else None


def parse_ids(ids: Optional[Union[gql.ID, list[gql.ID]]]) -> Optional[list[ObjectId]]:
    if ids is None:
        return None
    if ids is gql.UNSET:
        return None
    ids_set = ids if isinstance(ids, list) else [ids]
    parsed_ids = list[ObjectId]()
    for idx, cs in enumerate(ids_set):
        try:
            parsed_ids.append(ObjectId(cs))
        except (TypeError, InvalidId):
            raise ValueError(f"Invalid id[{idx}]: {cs}")
    return parsed_ids


async def resolve_merchant_paginated(
    id: Optional[Union[gql.ID, list[gql.ID]]] = gql.UNSET,
    limit: int = 20,
    cursor: Optional[Cursor] = gql.UNSET,
    sort: SortDirection = SortDirection.ASC,
) -> Connection[Merchant]:
    act_limit = limit + 1
    direction = "-" if sort is SortDirection.DESCENDING else "+"

    ids_set = parse_ids(id)
    cursor_id = parse_cursor(cursor)

    items_args = []
    if ids_set is not None and len(ids_set) > 0:
        items_args.append(OpIn(MerchantDB.id, ids_set))
    if cursor_id is not None:
        items_args.append(MerchantDB.id >= cursor_id)

    items = (
        await MerchantDB.find(
            *items_args,
        )
        .sort(f"{direction}_id")
        .limit(act_limit)
        .to_list()
    )
    if len(items) < 1:
        return Connection(
            _total=0,
            page_info=PageInfo(total_results=0, per_page=limit, next_cursor=None, has_next_page=False),
            nodes=[],
        )

    if ids_set is not None and len(ids_set) > 0:
        items_count = await MerchantDB.find(OpIn(MerchantDB.id, ids_set)).count()
    else:
        items_count = await MerchantDB.find().count()

    last_item = None
    if len(items) > limit:
        last_item = items.pop()
    next_cursor = last_item.id if last_item is not None else None
    has_next_page = next_cursor is not None

    mapped_items = [Merchant.from_db(item) for item in items]

    return Connection(
        _total=len(mapped_items),
        page_info=PageInfo(
            total_results=items_count,
            per_page=limit,
            next_cursor=to_cursor(next_cursor),
            has_next_page=has_next_page,
        ),
        nodes=mapped_items,
    )
