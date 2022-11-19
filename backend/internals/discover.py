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

# Autodiscover all routes

from __future__ import annotations

import logging
from importlib import util
from pathlib import Path
from typing import Any, Dict, Union

from fastapi import APIRouter, FastAPI

__all__ = ("discover_routes",)

logger = logging.getLogger("Internals.Discovery")


def discover_routes(
    app_or_router: Union[APIRouter, FastAPI], route_path: Path, recursive: bool = False, **router_kwargs: Dict[str, Any]
):
    routes_iter = route_path.glob("*.py") if not recursive else route_path.rglob("*.py")
    for route in routes_iter:
        if route.name == "__init__.py":
            continue
        logger.info(f"Loading route: {route.stem}")
        spec = util.spec_from_file_location(route.name, route)
        if spec is None:
            logger.warning(f"Failed to load route {route.name}")
            continue
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
        router_code = getattr(module, "router", None)
        if router_code is None:
            logger.warning(f'Failed to find "router" variable in {route.stem}')
            continue
        if not isinstance(router_code, APIRouter):
            logger.warning(f'"router" variable in {route.stem} is not an fastapi.APIRouter')
            continue
        logger.info(f'Attaching route "{route.stem}" to {app_or_router.prefix}')
        app_or_router.include_router(router_code, **router_kwargs)
