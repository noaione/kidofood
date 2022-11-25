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

from internals.db import AvatarImage
from internals.db import User as UserDB
from internals.session import encrypt_password, verify_password

from .models import User

__all__ = (
    "mutate_login_user",
    "mutate_register_user",
)


async def mutate_login_user(
    email: str,
    password: str,
):
    user = await UserDB.find_one(UserDB.email == email)
    if not user:
        return False, "User with associated email not found"

    is_verify, new_password = await verify_password(password, user.password)
    if not is_verify:
        return False, "Password is not correct"
    if new_password is not None and user is not None:
        user.password = new_password
        await user.save_changes()
    return True, User.from_db(user)


async def mutate_register_user(
    email: str,
    password: str,
    name: str,
):
    user = await UserDB.find_one(UserDB.email == email)
    if user:
        return False, "User with associated email already exists"

    hash_paas = await encrypt_password(password)
    new_user = UserDB(email=email, password=hash_paas, name=name, avatar=AvatarImage())
    await new_user.insert()
    return True, new_user
