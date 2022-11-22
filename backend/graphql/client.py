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

from typing import Optional, Union

import strawberry as gql
from strawberry.types import Info

from .context import KidoFoodContext
from .models import Connection, Merchant, User
from .resolvers import Cursor, SortDirection, resolve_merchant_paginated


@gql.type
class Query:
    @gql.field
    async def user(self, info: Info[KidoFoodContext, None]) -> User:
        if info.context.user is None:
            raise Exception("You are not logged in")

        return User.from_session(info.context.user)

    @gql.field
    async def merchants(
        self,
        id: Optional[Union[gql.ID, list[gql.ID]]] = gql.UNSET,
        limit: int = 20,
        cursor: Optional[Cursor] = gql.UNSET,
        sort: SortDirection = SortDirection.ASC,
    ) -> Connection[Merchant]:
        return await resolve_merchant_paginated(id=id, limit=limit, cursor=cursor, sort=sort)


@gql.type
class Mutation:
    pass


@gql.type
class Subscription:
    pass
