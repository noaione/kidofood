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
from typing import AsyncGenerator, cast

import strawberry as gql

from internals.db import FoodOrder as FoodOrderDB
from internals.pubsub import get_pubsub
from internals.utils import to_uuid
from .models import FoodOrderGQL

__all__ = ("subs_order_update",)


async def subs_order_update(id: gql.ID) -> AsyncGenerator[FoodOrderGQL, None]:
    verify_id = await FoodOrderDB.find_one(FoodOrderDB.order_id == to_uuid(id))
    if verify_id is None:
        return

    pubsub = get_pubsub()
    async for data in pubsub.listen(f"order:updated:{id}"):
        yield FoodOrderGQL.from_db(cast(FoodOrderDB, data))
