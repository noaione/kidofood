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

import asyncio
from dataclasses import dataclass
from mimetypes import guess_extension

import magic
from fastapi import UploadFile

from internals.storage import get_local_storage
from internals.utils import make_uuid

from .scalars import Upload

__all__ = (
    "InvalidMimeType",
    "get_file_mimetype",
    "handle_image_upload",
)


class InvalidMimeType(ValueError):
    def __init__(self, mime_type: str, expected_mimetype: str):
        self.mime_type = mime_type
        self.expected_mimetype = expected_mimetype
        super().__init__(f"Invalid mime type: {mime_type} (expected: {expected_mimetype})")


@dataclass
class UploadResult:
    filename: str
    extension: str
    file_size: int


async def get_file_mimetype(file: UploadFile):
    # Get current seek position
    loop = asyncio.get_event_loop()
    current_pos = file.file.tell()
    # Seek to start
    await file.seek(0)
    # Read first 2048 bytes
    data = await file.read(2048)
    # Seek back to original position
    await file.seek(current_pos)

    detect = await loop.run_in_executor(None, magic.from_buffer, data, True)
    return detect


async def handle_image_upload(file: Upload, uuid: str, image_type: str) -> UploadResult:
    """
    Handle file upload from GraphQL
    """
    if not isinstance(file, UploadFile):
        raise TypeError("Expected UploadFile, got %r" % file)

    # Handle upload
    stor = get_local_storage()
    mimetype = await get_file_mimetype(file)
    if not mimetype.startswith("image/"):
        raise InvalidMimeType(mimetype, "image/*")

    uuid_gen = str(make_uuid())
    extension = guess_extension(mimetype) or ".bin"
    filename = f"{uuid_gen}{extension}"

    # Upload file
    result = await stor.stream_upload(
        key=image_type,
        key_id=uuid,
        filename=filename,
        data=file,
    )
    if result is None:
        raise RuntimeError("Failed to upload file")
    return UploadResult(filename=uuid_gen, extension=extension, file_size=result.size)
