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
from uuid import UUID

from beanie.operators import Eq
from fastapi import APIRouter, Depends
from fastapi.datastructures import Default
from fastapi.responses import ORJSONResponse, Response

from internals.db import User
from internals.models import PartialLogin
from internals.responses import ResponseType
from internals.session import (
    PartialUserSession,
    UserSession,
    check_session_cookie,
    get_session_backend,
    get_session_cookie,
    get_session_verifier,
    verify_password,
)

__all__ = ("router",)
router = APIRouter(
    prefix="/user",
    tags=["User"],
    dependencies=[Depends(check_session_cookie)],
    default_response_class=Default(ORJSONResponse),
)
logger = logging.getLogger("Routes.User")


@router.get("/me")
async def auth_me(session: UserSession = Depends(get_session_verifier)):
    """
    Get current user's info
    """

    return ResponseType[PartialUserSession](data=session.to_partial()).to_orjson()


@router.post("/enter")
async def auth_enter(user: PartialLogin, response: Response):
    """
    Login and set session
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

    if new_password is not None:
        logger.warning(f"User {user.email} password hash is outdated, updating...")
        get_user.password = new_password
        await get_user.save_changes()

    logger.info(f"User {user.email} authenticated, setting session")
    session = UserSession.from_db(get_user, user.remember)
    backend = get_session_backend()
    await backend.create(session.session_id, session)
    get_session_cookie().attach_to_response(response, session.session_id)

    return ResponseType[PartialUserSession](data=session.to_partial()).to_orjson()


@router.post("/leave")
async def auth_leave(response: Response, session_id: UUID = Depends(check_session_cookie)):
    """
    Logout and remove session
    """

    backend = get_session_backend()
    await backend.delete(session_id=session_id)
    get_session_cookie().delete_from_response(response)

    return ResponseType().to_orjson()
