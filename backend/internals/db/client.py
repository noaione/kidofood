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
import time
from typing import TYPE_CHECKING

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

if TYPE_CHECKING:
    from motor.core import AgnosticClient, AgnosticDatabase

from .models import FoodItem, FoodOrder, Merchant, User

__all__ = ("KFDatabase",)


class KFDatabase:
    def __init__(
        self,
        ip_hostname_or_url: str,
        port: int = 27017,
        dbname: str = "kidofood",
        auth_string: str = None,
        auth_source: str = "admin",
        tls: bool = False,
    ):
        self.logger = logging.getLogger("KidoFood.Database")
        self.__ip_hostname_or_url = ip_hostname_or_url
        self._port = port
        self._dbname = dbname
        self._auth_string = auth_string
        self._auth_source = auth_source
        self._tls = tls

        self._url = self.__ip_hostname_or_url if self.__ip_hostname_or_url.startswith("mongodb") else ""
        self._ip_hostname = ""
        if self._url == "":
            self._ip_hostname = self.__ip_hostname_or_url
            self._generate_url()

        self._client: AgnosticClient = AsyncIOMotorClient(self._url)
        self._db: AgnosticDatabase = self._client[self._dbname]

    @property
    def db(self):
        return self._db

    def _generate_url(self):
        self._url = "mongodb"
        if self._tls:
            self._url += "+srv"
        self._url += "://"
        if self._auth_string:
            self._url += self._auth_string + "@"
        self._url += f"{self._ip_hostname}"
        if not self._tls:
            self._url += f":{self._port}"
        self._url += "/"
        self._url += f"?authSource={self._auth_source}&readPreference=primary&directConnection=true"
        if self._tls:
            self._url += "&retryWrites=true&w=majority"

    async def validate_connection(self):
        return await self._db.command({"ping": 1})

    async def ping_server(self):
        t1_ping = time.perf_counter()
        self.logger.info("pinging server...")
        try:
            res = await self.validate_connection()
            t2_ping = time.perf_counter()
            if "ok" in res and int(res["ok"]) == 1:
                return True, (t2_ping - t1_ping) * 1000
            return False, 99999
        except (ValueError, PyMongoError):
            return False, 99999

    async def connect(self):
        await init_beanie(
            database=self._db,
            document_models=[
                FoodItem,
                FoodOrder,
                Merchant,
                User,
            ],
        )
