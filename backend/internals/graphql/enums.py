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

import strawberry as gql

from internals.enums import ApprovalStatus, ItemType, OrderStatus, UserType

__all__ = (
    "ItemTypeGQL",
    "ApprovalStatusGQL",
    "UserTypeGQL",
    "OrderStatusGQL",
)

ItemTypeGQL = gql.enum(ItemType, name="ItemType", description="The item type")
UserTypeGQL = gql.enum(UserType, name="UserType", description="The user type")
ApprovalStatusGQL = gql.enum(ApprovalStatus, name="ApprovalStatus", description="The merchant approval status")
OrderStatusGQL = gql.enum(OrderStatus, name="OrderStatus", description="The order status")
