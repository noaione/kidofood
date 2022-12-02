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
from dataclasses import dataclass

from fastapi import APIRouter

from internals.db import User
from internals.enums import UserType
from internals.responses import ResponseType
from internals.session import PartialUserSession, encrypt_password

__all__ = ("router",)
router = APIRouter(prefix="/server", tags=["Server"])
logger = logging.getLogger("Routes.Server")


@dataclass
class PartialRegister:
    """A partial register object that is used to store the register information
    before the user is registered.
    """

    email: str
    password: str


@router.get("/claim", summary="Check server claim status", response_model=ResponseType[PartialUserSession])
async def claim_server_get():
    """
    Check if a server has been claimed or not.

    If the `data` is `null`, then the server has not been claimed yet.
    """

    logger.info("Checking server claim status...")
    user_claim = await User.find_one(User.type == UserType.ADMIN)
    if user_claim is None:
        return ResponseType[PartialUserSession]().to_orjson()
    return ResponseType[PartialUserSession](data=PartialUserSession.from_db(user_claim)).to_orjson()


@router.post("/claim", summary="Claim server", response_model=ResponseType[PartialUserSession])
async def claim_server_post(user: PartialRegister):
    """
    Claim a server for a user.
    """

    logger.info("Checking server claim status...")
    user_claim = await User.find_one(User.type == UserType.ADMIN)
    if user_claim is not None:
        logger.info("Server has been claimed.")
        return ResponseType[PartialUserSession](
            error="User already claimed this server!", code=403, data=PartialUserSession.from_db(user_claim)
        ).to_orjson(403)

    logger.info(f"Claiming with {user.email}...")
    hash_pass = await encrypt_password(user.password)
    user_new = User(
        name="Admin",
        email=user.email,
        password=hash_pass,
        type=UserType.ADMIN,
    )
    await user_new.insert()
    user_sess = PartialUserSession.from_db(user_new)
    logger.info(f"User {user.email} created, responding...")

    return ResponseType[PartialUserSession](data=user_sess).to_orjson()
