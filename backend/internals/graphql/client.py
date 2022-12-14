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

from typing import AsyncGenerator, Optional, Union, cast
from uuid import UUID

import strawberry as gql
from strawberry.file_uploads import Upload
from strawberry.types import Info

from internals.db import Merchant as MerchantDB
from internals.session import UserSession

from .context import KidoFoodContext
from .enums import ApprovalStatusGQL, OrderStatusGQL, UserTypeGQL
from .models import (
    Connection,
    FoodItemGQL,
    FoodItemInputGQL,
    FoodOrderGQL,
    FoodOrderItemInputGQL,
    MerchantGQL,
    MerchantInputGQL,
    PaymentMethodGQL,
    UserGQL,
    UserInputGQL,
)
from .mutations import (
    mutate_apply_new_merchant,
    mutate_login_user,
    mutate_make_new_order,
    mutate_new_food_item,
    mutate_register_user,
    mutate_update_merchant,
    mutate_update_order_status,
    mutate_update_user,
)
from .resolvers import (
    Cursor,
    SortDirection,
    resolve_food_items_paginated,
    resolve_food_order_paginated,
    resolve_merchant_paginated,
    resolve_user_from_db,
)
from .scalars import UUID as UUID2
from .scalars import Upload as UploadGQL
from .subscriptions import subs_order_update

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
        status: list[ApprovalStatusGQL] = [ApprovalStatusGQL.APPROVED],
    ) -> Connection[MerchantGQL]:
        return await resolve_merchant_paginated(query=query, limit=limit, cursor=cursor, sort=sort, status=status)

    @gql.field(description="Search for food items by name")
    async def items(
        self,
        query: str,
        limit: int = 20,
        cursor: Optional[Cursor] = gql.UNSET,
        sort: SortDirection = SortDirection.ASC,
    ) -> Connection[FoodItemGQL]:
        return await resolve_food_items_paginated(query=query, limit=limit, cursor=cursor, sort=sort)


@gql.type
class Query:
    @gql.field(description="Get the current user")
    async def user(self, info: Info[KidoFoodContext, None]) -> UserGQL:
        if info.context.user is None:
            raise Exception("You are not logged in")

        user = await resolve_user_from_db(UserGQL.from_session(info.context.user))
        return UserGQL.from_db(user)

    @gql.field(description="Get single or multiple merchants")
    async def merchants(
        self,
        id: Optional[list[gql.ID]] = gql.UNSET,
        limit: int = 20,
        cursor: Optional[Cursor] = gql.UNSET,
        sort: SortDirection = SortDirection.ASC,
        status: list[ApprovalStatusGQL] = [ApprovalStatusGQL.APPROVED],
    ) -> Connection[MerchantGQL]:
        return await resolve_merchant_paginated(id=id, limit=limit, cursor=cursor, sort=sort, status=status)

    @gql.field(description="Get single or multiple food items")
    async def items(
        self,
        id: Optional[list[gql.ID]] = gql.UNSET,
        limit: int = 20,
        cursor: Optional[Cursor] = gql.UNSET,
        sort: SortDirection = SortDirection.ASC,
    ) -> Connection[FoodItemGQL]:
        return await resolve_food_items_paginated(id=id, limit=limit, cursor=cursor, sort=sort)

    @gql.field(description="Get single or multiple food orders")
    async def orders(
        self,
        id: Optional[list[gql.ID]] = gql.UNSET,
        limit: int = 20,
        cursor: Optional[Cursor] = gql.UNSET,
        sort: SortDirection = SortDirection.ASC,
    ) -> Connection[FoodOrderGQL]:
        return await resolve_food_order_paginated(id=id, limit=limit, cursor=cursor, sort=sort)

    search: QuerySearch = gql.field(description="Search for items on specific fields")


ItemResult = gql.union(
    "ItemResult", (Result, FoodItemGQL), description="Either `FoodItem` if success or `Result` if failure detected"
)
MerchantResult = gql.union(
    "MerchantResult", (Result, MerchantGQL), description="Either `Merchant` if success or `Result` if failure detected"
)
OrderResult = gql.union(
    "OrderResult", (Result, FoodOrderGQL), description="Either `FoodOrder` if success or `Result` if failure detected"
)
UserResult = gql.union(
    "UserResult", (Result, UserGQL), description="Either `User` if success or `Result` if failure detected"
)


@gql.type
class Mutation:
    @gql.mutation(description="Login to KidoFood")
    async def login_user(self, email: str, password: str, info: Info[KidoFoodContext, None]) -> UserResult:
        if info.context.user is not None:
            return Result(success=False, message="You are already logged in")
        success, user = await mutate_login_user(email, password)
        if not success and isinstance(user, str):
            return Result(success=False, message=user)
        user_info = cast(UserGQL, user)
        info.context.session_latch = True
        info.context.user = user_info.to_session()
        return user_info

    @gql.mutation(description="Logout from KidoFood")
    async def logout_user(self, info: Info[KidoFoodContext, None]) -> Result:
        if info.context.user is None:
            return Result(success=False, message="You are not logged in")
        info.context.session_latch = True
        info.context.user = None
        return Result(success=True, message=None)

    @gql.mutation(description="Register to KidoFood")
    async def register_user(
        self,
        info: Info[KidoFoodContext, None],
        email: str,
        password: str,
        name: str,
        type: UserTypeGQL = UserTypeGQL.CUSTOMER,
    ) -> UserResult:
        if info.context.user is not None:
            raise Exception("Please logout first before registering as new user")
        if type not in (UserTypeGQL.CUSTOMER, UserTypeGQL.RIDER):
            return Result(success=False, message="User type is not supported")
        success, user = await mutate_register_user(email, password, name, type)
        if not success and isinstance(user, str):
            return Result(success=False, message=user)
        user_info = cast(UserGQL, user)
        return user_info

    @gql.mutation(description="Apply for merchant")
    async def apply_merchant(
        self,
        info: Info[KidoFoodContext, None],
        merchant: MerchantInputGQL,
    ) -> MerchantResult:
        if info.context.user is None:
            raise Exception("You are not logged in")
        user = UserGQL.from_session(info.context.user)
        is_success, new_merchant, userchange = await mutate_apply_new_merchant(
            user=user,
            merchant=merchant,
        )
        if not is_success and isinstance(new_merchant, str):
            return Result(success=False, message=new_merchant)
        if userchange is not None:
            user_data = UserSession.from_db(userchange, True)
            info.context.session_latch = True
            info.context.user = user_data
        return MerchantGQL.from_db(cast(MerchantDB, new_merchant))

    @gql.mutation(description="Update merchant information")
    async def update_merchant(
        self,
        info: Info[KidoFoodContext, None],
        id: gql.ID,
        merchant: MerchantInputGQL,
    ) -> MerchantResult:
        if info.context.user is None:
            raise Exception("You are not logged in")
        user = UserGQL.from_session(info.context.user)
        is_success, update_merchant = await mutate_update_merchant(
            id=id,
            user=user,
            merchant=merchant,
        )
        if not is_success and isinstance(update_merchant, str):
            return Result(success=False, message=update_merchant)
        return MerchantGQL.from_db(cast(MerchantDB, update_merchant))

    @gql.mutation(description="Update user information, you must be logged in to update your own account")
    async def update_user(
        self,
        info: Info[KidoFoodContext, None],
        user: UserInputGQL,
    ) -> UserResult:
        if info.context.user is None:
            raise Exception("You are not logged in")
        user_acc = UserGQL.from_session(info.context.user)
        is_success, update_user = await mutate_update_user(
            id=cast(gql.ID, str(user_acc.id)),
            user=user,
        )
        if not is_success and isinstance(update_user, str):
            return Result(success=False, message=update_user)
        return cast(UserGQL, update_user)

    @gql.mutation(description="Make a new food order")
    async def new_order(
        self,
        info: Info[KidoFoodContext, None],
        items: list[FoodOrderItemInputGQL],
        payment: PaymentMethodGQL,
    ) -> OrderResult:
        if info.context.user is None:
            raise Exception("You are not logged in")
        user = UserGQL.from_session(info.context.user)
        if user.type != UserTypeGQL.CUSTOMER:
            return Result(success=False, message="You are not a customer")
        if len(items) < 1:
            return Result(success=False, message="You must order at least 1 item")
        _, order_or_str = await mutate_make_new_order(user, items, payment)
        if isinstance(order_or_str, str):
            return Result(success=False, message=order_or_str)
        return order_or_str

    @gql.mutation(description="Update food order")
    async def update_order(
        self,
        info: Info[KidoFoodContext, None],
        id: gql.ID,
        status: OrderStatusGQL,
    ) -> OrderResult:
        if info.context.user is None:
            raise Exception("You are not logged in")
        _, order_or_str = await mutate_update_order_status(id, status)
        if isinstance(order_or_str, str):
            return Result(success=False, message=order_or_str)
        return order_or_str

    @gql.mutation(description="Create new food item")
    async def create_item(
        self,
        info: Info[KidoFoodContext, None],
        item: FoodItemInputGQL,
    ) -> ItemResult:
        if info.context.user is None:
            raise Exception("You are not logged in")
        user = UserGQL.from_session(info.context.user)
        _, item_or_str = await mutate_new_food_item(user, item)
        if isinstance(item_or_str, str):
            return Result(success=False, message=item_or_str)
        return item_or_str


@gql.type
class Subscription:
    @gql.subscription(description="Subscribe to food orders updates")
    async def order_update(self, info: Info[KidoFoodContext, None], id: gql.ID) -> AsyncGenerator[FoodOrderGQL, None]:
        if info.context.user is None:
            raise Exception("You are not logged in")
        async for order in subs_order_update(id):
            yield order


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

schema = gql.Schema(
    **_schema_params,
    scalar_overrides={
        UUID: UUID2,
        Upload: UploadGQL,
    },
)
