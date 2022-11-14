import asyncio
from io import BytesIO
from typing import cast

from minio import Minio
from minio.datatypes import Object
from minio.helpers import ObjectWriteResult
from urllib3.response import HTTPResponse

__all__ = ("S3BucketServer", "get_s3_or_local", "create_s3_server")


class S3BucketServer:
    def __init__(
        self,
        hostname: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        *,
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop(),
    ):
        self._m = Minio(
            hostname,
            access_key=access_key,
            secret_key=secret_key,
        )
        self._loop = loop
        self._bucket = bucket_name

    async def start(self):
        exist = await self._loop.run_in_executor(None, self._m.bucket_exists, self._bucket)
        if not exist:
            raise RuntimeError(f"Bucket {self._bucket} does not exist")

    def close(self):
        self._m._http.clear()

    async def stream_upload(self, key: str, key_id: str, filename: str, data: BytesIO, type: str = "images"):
        path = f"{type}/{key}/{key_id.replace('-', '')}/{filename}"
        result = await self._loop.run_in_executor(None, self._m.put_object, self._bucket, path, data)
        return cast(ObjectWriteResult, result)

    async def stat_file(self, key: str, key_id: str, filename: str, type: str = "images"):
        path = f"{type}/{key}/{key_id.replace('-', '')}/{filename}"
        try:
            data = await self._loop.run_in_executor(None, self._m.stat_object, self._bucket, path)
            return cast(Object, data)
        except Exception:
            return None

    async def exists(self, key: str, key_id: str, filename: str, type: str = "images"):
        return await self.stat_file(key, key_id, filename, type) is not None

    async def stream_download(self, key: str, key_id: str, filename: str, type: str = "images"):
        path = f"{type}/{key}/{key_id.replace('-', '')}/{filename}"
        data: HTTPResponse = await self._loop.run_in_executor(None, self._m.get_object, self._bucket, path)
        while True:
            chunk = await self._loop.run_in_executor(None, data.read, 1024)
            if not chunk:
                break
            yield chunk

    async def download(self, key: str, key_id: str, filename: str, type: str = "images"):
        path = f"{type}/{key}/{key_id.replace('-', '')}/{filename}"
        data: HTTPResponse = await self._loop.run_in_executor(None, self._m.get_object, self._bucket, path)
        return await self._loop.run_in_executor(None, data.read, None, None, True)

    async def delete(self, key: str, key_id: str, filename: str, type: str = "images"):
        path = f"{type}/{key}/{key_id.replace('-', '')}/{filename}"
        await self._loop.run_in_executor(None, self._m.remove_object, self._bucket, path)


_S3SESSION: S3BucketServer = None


async def create_s3_server(hostname: str, access_key: str, secret_key: str, bucket_name: str):
    global _S3SESSION
    if _S3SESSION is not None:
        raise RuntimeError("S3 server already created")
    _S3SESSION = S3BucketServer(hostname, access_key, secret_key, bucket_name)
    await _S3SESSION.start()


def get_s3_or_local():
    if _S3SESSION is None:
        return None
    return _S3SESSION
