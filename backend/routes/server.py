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
import logging
import os
import platform
import time
from dataclasses import dataclass
from typing import TypedDict

import psutil
from fastapi import APIRouter
from fastapi import __version__ as fastapi_version

from internals.db import User
from internals.enums import UserType
from internals.responses import ResponseType
from internals.session import PartialUserSession, encrypt_password
from internals.version import __version__ as kf_version

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


class _MemoryStatsResult(TypedDict):
    real: float
    virtual: float


class StatsResult(TypedDict):
    os: str
    """The OS host"""
    python: str
    """The Python version used"""
    fastapi: str
    """The fastapi version"""
    version: str
    """The current app version"""
    memory: _MemoryStatsResult
    """Memory stats in MiB"""
    uptime: float
    """The uptime in seconds"""


@router.get("/status", summary="Check server health and status", response_model=ResponseType[StatsResult])
async def server_status():
    """
    Check server health and status.
    """
    loop = asyncio.get_event_loop()

    # Get used CPU and memory by the server
    process = await loop.run_in_executor(None, psutil.Process, os.getpid())
    mem_info = await loop.run_in_executor(None, process.memory_info)
    rss_mem = round(mem_info.rss / 1024**2, 2)
    vms_mem = round(mem_info.vms / 1024**2, 2)
    create_time = await loop.run_in_executor(None, process.create_time)

    delta_uptime = time.time() - create_time

    os_system = f"{platform.system()} {platform.release()}"
    py_ver = platform.python_version()

    data_res: StatsResult = {
        "os": os_system,
        "python": py_ver,
        "fastapi": fastapi_version,
        "version": kf_version,
        "memory": {"real": rss_mem, "virtual": vms_mem},
        "uptime": delta_uptime,
    }

    return ResponseType[StatsResult](data=data_res).to_orjson()
