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

from beanie.operators import Eq
from fastapi import APIRouter, Depends

from internals.db import User
from internals.models import PartialLogin, PartialRegister
from internals.responses import ResponseType
from internals.session import (
    PartialUserSession,
    UserSession,
    check_session,
    encrypt_password,
    get_session_handler,
    verify_password,
)

__all__ = ("router",)
router = APIRouter(prefix="/user", tags=["User"])
logger = logging.getLogger("Routes.User")


@router.get(
    "/me",
    summary="Get current user",
    response_model=ResponseType[PartialUserSession],
)
async def auth_me(session: UserSession = Depends(check_session)):
    """
    This route will return the current user information from the cookie
    information.
    """

    return ResponseType[PartialUserSession](data=session.to_partial()).to_orjson()


@router.post("/enter", summary="Login to KidoFood", response_model=ResponseType[PartialUserSession])
async def auth_enter(user: PartialLogin):
    """
    This route will try to login the user with the given information.
    """

    logger.info(f"Trying to authenticate {user.email} with {user.password}")
    get_user = await User.find(Eq(User.email, user.email)).first_or_none()
    if get_user is None:
        logger.error(f"User {user.email} not found")
        return ResponseType(error="User not found", code=401).to_orjson(401)

    logger.info(f"User {user.email} found, verifying password")
    is_verify, new_password = await verify_password(user.password, get_user.password)
    if not is_verify:
        logger.error(f"User {user.email} password not match")
        return ResponseType(error="Password is incorrect", code=401).to_orjson(401)

    if new_password is not None and get_user is not None:
        logger.warning(f"User {user.email} password hash is outdated, updating...")
        get_user.password = new_password
        await get_user.save_changes()

    logger.info(f"User {user.email} authenticated, setting session")
    session = UserSession.from_db(get_user, user.remember)
    json_resp = ResponseType[PartialUserSession](data=session.to_partial()).to_orjson()
    handler = get_session_handler()
    await handler.set_session(session, json_resp)

    return json_resp


@router.post("/leave", summary="Logout from KidoFood", response_model=ResponseType)
async def auth_leave(session: UserSession = Depends(check_session)):
    """
    This route will remove your current session.
    """

    handler = get_session_handler()
    default_resp = ResponseType().to_orjson()
    await handler.remove_session(session.session_id, default_resp)

    return default_resp


@router.post(
    "/register",
    summary="Register to KidoFood",
    response_model=ResponseType[PartialUserSession],
)
async def auth_register(user: PartialRegister):
    """
    This route will try to register the user with the given information.
    """

    logger.info(f"Trying to register {user.email} with {user.password}")
    get_user = await User.find(Eq(User.email, user.email)).first_or_none()
    if get_user is not None:
        logger.error(f"User {user.email} already exists")
        return ResponseType(error="User already exists", code=409).to_orjson(409)

    logger.info(f"User {user.email} not found, creating new user")
    hash_pass = await encrypt_password(user.password)
    new_user = User(email=user.email, name=user.name, password=hash_pass, avatar="")
    await new_user.insert()
    user_sess = PartialUserSession.from_db(new_user)
    logger.info(f"User {user.email} created, responding...")

    return ResponseType[PartialUserSession](data=user_sess).to_orjson()
