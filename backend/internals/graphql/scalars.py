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

from typing import NewType
from uuid import UUID as UUIDMod  # noqa: N811

import strawberry as gql

__all__ = (
    "UUID",
    "Upload",
    "UploadType",
)


UploadType = NewType("Upload", bytes)
UUID = gql.scalar(
    UUIDMod,
    name="UUID",
    description="An UUID4 formatted string",
    serialize=lambda x: str(x),
    parse_value=lambda x: UUIDMod(x),
)

Upload = gql.scalar(
    UploadType,
    name="Upload",
    description="A file to be uploaded (`bytes` data) [mutation only]",
    parse_value=lambda x: x,
)
