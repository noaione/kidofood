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
from typing import Optional, Union

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

__all__ = (
    "get_argon2",
    "encrypt_password",
    "verify_password",
)


Hashable = Union[str, bytes]
_ARGON2_HASHER = PasswordHasher()


def get_argon2() -> PasswordHasher:
    return _ARGON2_HASHER


async def encrypt_password(password: Hashable, *, loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()):
    if not isinstance(password, bytes):
        password = password.encode("utf-8")

    hashed = await loop.run_in_executor(None, get_argon2().hash, password)
    return hashed


async def verify_password(
    password: str, hashed_password: str, *, loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
) -> tuple[bool, Optional[str]]:
    """
    Verify the password with hashed argon2 password.
    Return a tuple of (is_verified, new_hashed_password)
    """

    try:
        is_correct = await loop.run_in_executor(None, get_argon2().verify, hashed_password, password)
    except VerifyMismatchError:
        is_correct = False
    if is_correct:
        need_rehash = await loop.run_in_executor(None, get_argon2().check_needs_rehash, hashed_password)
        if need_rehash:
            new_hashed = await encrypt_password(password, loop=loop)
            return True, new_hashed
        return True, None
    return False, None
