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
from typing import get_args

import pendulum
from beanie import Document
from pydantic.typing import resolve_annotations

__all__ = ("DocumentX",)


class DocumentX(Document):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Check if the date is a pendulum instance or not
        self._coerce_to_pendulum()

    def _coerce_to_pendulum(self):
        # Get annotation list, and check if it's DateTime instance
        # If it is, then check if it's a pendulum instance or not

        annotations = self.__annotations__
        annotate = resolve_annotations(annotations, None)

        for key, type_t in annotate.items():
            act_type = type_t
            type_arg = get_args(type_t)
            if len(type_arg) > 0:
                act_type = type_arg[0]

            # check if it's pendulum class type
            if issubclass(act_type, pendulum.DateTime):
                # Coerce to pendulum instance
                current = object.__getattribute__(self, key)
                if current is None:
                    continue
                if isinstance(current, pendulum.DateTime):
                    continue
                if isinstance(current, str):
                    # Assume ISO8601 format
                    object.__setattr__(self, key, pendulum.parse(current))
                elif isinstance(current, (int, float)):
                    # Unix timestamp
                    object.__setattr__(self, key, pendulum.from_timestamp(current))
                elif isinstance(current, datetime):
                    object.__setattr__(self, key, pendulum.instance(current))
