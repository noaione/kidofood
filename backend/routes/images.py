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

import logging
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import Response, StreamingResponse

from internals.storage import get_s3_or_local

__all__ = ("router",)
router = APIRouter(prefix="/images", tags=["Images"])
logger = logging.getLogger("Routes.Images")

ImageType = Literal["merchant", "items", "users"]


@router.get("/{type}/{id}/{key}", summary="Get specific image key")
async def get_image(type: ImageType, id: str, key: str):
    # Key can include or not include the extension.

    logger.info("Getting image %s/%s/%s", type, id, key)

    storages = get_s3_or_local()
    stat_file = await storages.stat_file(key=type, key_id=id, filename=key)
    if stat_file is None:
        logger.error("Unable to find specified image: %s/%s/%s", type, id, key)
        return Response(status_code=404, content="Not Found", media_type="text/plain")

    async def image_streamer():
        async for chunk in storages.stream_download(key=type, key_id=id, filename=key):
            yield chunk

    logger.info("Image found, streaming back response to user...")
    return StreamingResponse(image_streamer(), media_type=stat_file.content_type)
