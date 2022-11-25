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

from typing import Optional, Union, cast
from uuid import UUID

import strawberry as gql
from strawberry.types import Info

from .context import KidoFoodContext
from .models import Connection, FoodItem, FoodOrder, Merchant, User
from .mutations import mutate_login_user, mutate_register_user
from .resolvers import (
    Cursor,
    SortDirection,
    resolve_food_items_paginated,
    resolve_food_order_paginated,
    resolve_merchant_paginated,
)
from .scalars import UUID as UUID2

__all__ = (
    "Query",
    "Mutation",
    "Subscription",
    "schema",
)


@gql.type(description="Simple result of mutation")
class Result:
    success: bool = gql.field(description="Success status")
    message: Optional[str] = gql.field(description="Extra message if any, might be available if success is False")


@gql.type(description="Search for items on specific fields")
class QuerySearch:
    @gql.field(description="Search for merchants by name")
    async def merchants(
        self,
        query: str,
        limit: int = 20,
        cursor: Optional[Cursor] = gql.UNSET,
        sort: SortDirection = SortDirection.ASC,
    ) -> Connection[Merchant]:
        return await resolve_merchant_paginated(query=query, limit=limit, cursor=cursor, sort=sort)

    @gql.field(description="Search for food items by name")
    async def items(
        self,
        query: str,
        limit: int = 20,
        cursor: Optional[Cursor] = gql.UNSET,
        sort: SortDirection = SortDirection.ASC,
    ) -> Connection[FoodItem]:
        return await resolve_food_items_paginated(query=query, limit=limit, cursor=cursor, sort=sort)


@gql.type
class Query:
    @gql.field(description="Get the current user")
    async def user(self, info: Info[KidoFoodContext, None]) -> User:
        if info.context.user is None:
            raise Exception("You are not logged in")

        return User.from_session(info.context.user)

    @gql.field(description="Get single or multiple merchants")
    async def merchants(
        self,
        id: Optional[list[gql.ID]] = gql.UNSET,
        limit: int = 20,
        cursor: Optional[Cursor] = gql.UNSET,
        sort: SortDirection = SortDirection.ASC,
    ) -> Connection[Merchant]:
        return await resolve_merchant_paginated(id=id, limit=limit, cursor=cursor, sort=sort)

    @gql.field(description="Get single or multiple food items")
    async def items(
        self,
        id: Optional[list[gql.ID]] = gql.UNSET,
        limit: int = 20,
        cursor: Optional[Cursor] = gql.UNSET,
        sort: SortDirection = SortDirection.ASC,
    ) -> Connection[FoodItem]:
        return await resolve_food_items_paginated(id=id, limit=limit, cursor=cursor, sort=sort)

    @gql.field(description="Get single or multiple food orders")
    async def orders(
        self,
        id: Optional[list[gql.ID]] = gql.UNSET,
        limit: int = 20,
        cursor: Optional[Cursor] = gql.UNSET,
        sort: SortDirection = SortDirection.ASC,
    ) -> Connection[FoodOrder]:
        return await resolve_food_order_paginated(id=id, limit=limit, cursor=cursor, sort=sort)

    search: QuerySearch = gql.field(description="Search for items on specific fields")


UserResult = gql.union(
    "UserResult", (Result, User), description="Either `User` if success or `Result` if failure detected"
)


@gql.type
class Mutation:
    @gql.field(description="Login to KidoFood")
    async def login_user(self, email: str, password: str, info: Info[KidoFoodContext, None]) -> UserResult:
        if info.context.user is not None:
            return Result(success=False, message="You are already logged in")
        success, user = await mutate_login_user(email, password)
        if not success and isinstance(user, str):
            return Result(success=False, message=user)
        user_info = cast(User, user)
        info.context.session_latch = True
        info.context.user = user_info.to_session()
        return user_info

    @gql.field(description="Logout from KidoFood")
    async def logout_user(self, info: Info[KidoFoodContext, None]) -> Result:
        if info.context.user is None:
            return Result(success=False, message="You are not logged in")
        info.context.session_latch = True
        info.context.user = None
        return Result(success=True, message=None)

    @gql.field(description="Register to KidoFood")
    async def register_user(
        self, email: str, password: str, name: str, info: Info[KidoFoodContext, None]
    ) -> UserResult:
        if info.context.user is not None:
            raise Exception("Please logout first before registering as new user")
        success, user = await mutate_register_user(email, password, name)
        if not success and isinstance(user, str):
            return Result(success=False, message=user)
        user_info = cast(User, user)
        return user_info


@gql.type
class Subscription:
    pass


def _has_any_function_or_attr(obj: Union[type, object]) -> bool:
    any_function = any((callable(getattr(obj, name, None)) for name in dir(obj) if not name.startswith("_")))
    annotations = getattr(obj, "__annotations__", None)
    any_attr = annotations is not None and len(annotations) > 0
    return any_function or any_attr


_schema_params = {
    "query": Query,
    "mutation": None,
    "subscription": None,
}
if _has_any_function_or_attr(Mutation):
    _schema_params["mutation"] = Mutation
if _has_any_function_or_attr(Subscription):
    _schema_params["subscription"] = Subscription

schema = gql.Schema(**_schema_params, scalar_overrides={UUID: UUID2})
