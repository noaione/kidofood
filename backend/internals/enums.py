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

__all__ = (
    "ItemType",
    "ApprovalStatus",
    "UserType",
    "OrderStatus",
    "AvatarType",
)


class ItemType(str, Enum):
    DRINK = "drink"
    MEAL = "meal"
    PACKAGE = "package"


class ApprovalStatus(str, Enum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"


class UserType(int, Enum):
    CUSTOMER = 0
    """Customer"""
    MERCHANT = 1
    """Merchant (not used right now)"""
    RIDER = 2
    """Rider or driver"""
    ADMIN = 999
    """Administrator"""


class OrderStatus(int, Enum):
    # Pending payment
    PENDING = 0
    # Payment is done, submitted to merchant
    FORWARDED = 1
    # Merchant accepted the order, processing
    ACCEPTED = 2
    # Merchant processing the order
    PROCESSING = 3
    # Merchant finished processing the order, delivery
    DELIVERING = 4
    # Merchant rejected the order
    REJECTED = 100
    # User cancelled the order
    CANCELLED = 101
    # Merchant canceled the order
    CANCELED_MERCHANT = 102
    # Problem with the order
    # merchant problem
    PROBLEM_MERCHANT = 103
    # user problem
    PROBLEM_FAIL_TO_DELIVER = 104
    # Order is complete
    DONE = 200


class AvatarType:
    USERS = "user"
    MERCHANT = "merchant"
    ITEMS = "items"
