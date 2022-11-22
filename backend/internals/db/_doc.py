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

---

A custom Document class for Beanie, with support of coercing Pendulum DateTime object.
"""

from __future__ import annotations

from datetime import datetime
from functools import partial as ftpartial
from typing import ForwardRef, get_args

import pendulum
from beanie import Document
from pendulum.datetime import DateTime
from pendulum.parser import parse as pendulum_parse
from pydantic.typing import resolve_annotations

__all__ = (
    "_coerce_to_pendulum",
    "pendulum_utc",
)
pendulum_utc = ftpartial(pendulum.now, tz="UTC")


def _unpack_forwardref(annotation):
    if isinstance(annotation, ForwardRef):
        return annotation.__forward_arg__
    return annotation


def _coerce_to_pendulum(clss: Document):
    # Get annotation list, and check if it's DateTime instance
    # If it is, then check if it's a pendulum instance or not

    annotations = clss.__annotations__
    annotate = resolve_annotations(annotations, None)

    for key, type_t in annotate.items():
        act_type = type_t
        type_arg = get_args(type_t)
        if len(type_arg) > 0:
            act_type = type_arg[0]
        fwd_unpack = _unpack_forwardref(act_type)

        try:
            is_pdt_type = issubclass(act_type, DateTime) or "pendulum.DateTime" in str(fwd_unpack)
        except Exception:
            is_pdt_type = "pendulum.DateTime" in str(fwd_unpack)
            if not is_pdt_type:
                continue

        # check if it's pendulum class type
        if is_pdt_type:
            # Coerce to pendulum instance
            current = object.__getattribute__(clss, key)
            if current is None:
                continue
            if isinstance(current, DateTime):
                continue
            if isinstance(current, str):
                # Assume ISO8601 format
                object.__setattr__(clss, key, pendulum_parse(current))
            elif isinstance(current, (int, float)):
                # Unix timestamp
                object.__setattr__(clss, key, pendulum.from_timestamp(current))
            elif isinstance(current, datetime):
                object.__setattr__(clss, key, pendulum.instance(current))
