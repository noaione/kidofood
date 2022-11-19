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

from pathlib import Path
from textwrap import dedent
from typing import Any, Union, overload
from uuid import UUID, uuid4

__all__ = (
    "make_uuid",
    "to_uuid",
    "to_boolean",
    "get_version",
    "get_description",
)

# Backend root
ROOT_PATH = Path(__file__).absolute().parent.parent


@overload
def make_uuid(stringify: bool = False) -> UUID:
    ...


@overload
def make_uuid(stringify: bool = True) -> str:
    ...


def make_uuid(stringify: bool = True) -> Union[str, UUID]:
    m = uuid4()
    return str(m) if stringify else m


def to_uuid(uuid: str) -> UUID:
    try:
        return UUID(uuid)
    except ValueError:
        raise ValueError("Invalid UUID")


def to_boolean(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower() in ("yes", "true", "t", "y", "1")
    return bool(value)


def get_version():
    pyproject = ROOT_PATH / "pyproject.toml"
    pyproject_data = pyproject.read_text().split("\n\n")

    version = None
    for section in pyproject_data:
        if section.startswith("[tool.poetry]"):
            for line in section.splitlines():
                if line.startswith("version ="):
                    version = line.split("=")[1].strip().strip('"')
                    break
    return version


def get_description():
    description = """Welcome to KidoFood API Documentation

    Source Code: [noaione/kidofood](https://github.com/noaione/kidofood)

    This documentation serves as a guide for developers who want to use KidoFood API.
    For their own application. This documentation is still in development and will be
    updated regularly. If you have any questions, please contact me on GitHub Issue on
    the link above.

    Written with [FastAPI](https://fastapi.tiangolo.com/)

    ## Changelog
    - 0.1.0
        - Initial Release
    """

    return dedent(description)
