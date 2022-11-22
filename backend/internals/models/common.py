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

from dataclasses import dataclass
from datetime import datetime
from functools import partial as ftpartial
from typing import Any

import pendulum
from pendulum.parser import parse as pendulum_parse
from pendulum.datetime import DateTime
from pendulum.date import Date
from pendulum.time import Time

from internals.db import AvatarImage

__all__ = (
    "pendulum_utc",
    "AvatarType",
    "AvatarResponse",
    "PartialID",
    "PartialIDName",
    "PartialIDAvatar",
    "_coerce_to_pendulum",
)
pendulum_utc = ftpartial(pendulum.now, tz="UTC")


def _coerce_to_pendulum(data: Any):
    if isinstance(data, str):
        parsed = pendulum_parse(data)
        if parsed is None:
            raise ValueError(f"Cannot parse {data} to pendulum.DateTime")
        if isinstance(parsed, DateTime):
            return parsed
        if isinstance(parsed, Date):
            return DateTime.combine(parsed, Time(0, 0, 0, 0, tzinfo=pendulum_utc().tz))
        if isinstance(parsed, Time):
            return DateTime.combine(pendulum_utc().date(), parsed)
    if isinstance(data, int):
        return pendulum.from_timestamp(data)
    if isinstance(data, datetime):
        return pendulum.instance(data)
    return None


class AvatarType:
    USERS = "user"
    MERCHANT = "merchant"
    ITEMS = "items"


@dataclass
class AvatarResponse:
    name: str
    type: str

    @classmethod
    def from_db(cls, avatar: AvatarImage, type: str):
        return cls(
            name=f"{avatar.key}.{avatar.format}",
            type=type,
        )


@dataclass
class PartialID:
    id: str


@dataclass
class PartialIDName(PartialID):
    name: str


@dataclass
class PartialIDAvatar(PartialIDName):
    avatar: AvatarResponse
