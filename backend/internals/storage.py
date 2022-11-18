import asyncio
from abc import abstractmethod
from dataclasses import dataclass
from io import BytesIO
from mimetypes import guess_type
from pathlib import Path
from typing import Optional, Union, cast

import pendulum
from aiopath import AsyncPath
from minio import Minio
from minio.datatypes import Object
from minio.helpers import ObjectWriteResult
from urllib3.response import HTTPResponse

__all__ = (
    "S3BucketServer",
    "get_s3_or_local",
    "get_local_storage",
    "create_s3_server",
)


@dataclass
class FileObject:
    filename: str
    content_type: str
    size: int
    last_modified: Optional[pendulum.DateTime] = None


class AbstractStorage:
    def __init__(self):
        pass

    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    async def stream_upload(self, key: str, key_id: str, filename: str, data: BytesIO, type: str = "images"):
        pass

    @abstractmethod
    async def stat_file(self, key: str, key_id: str, filename: str, type: str = "images"):
        pass

    @abstractmethod
    async def exists(self, key: str, key_id: str, filename: str, type: str = "images"):
        pass

    @abstractmethod
    async def stream_download(self, key: str, key_id: str, filename: str, type: str = "images"):
        pass

    @abstractmethod
    async def download(self, key: str, key_id: str, filename: str, type: str = "images"):
        pass

    @abstractmethod
    async def delete(self, key: str, key_id: str, filename: str, type: str = "images"):
        pass


class S3BucketServer(AbstractStorage):
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
            data2 = cast(Object, data)
            ldt = data2.last_modified
            if ldt is not None:
                ldt = pendulum.instance(ldt)
            return FileObject(path, data2.content_type, data2.size, ldt)
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


class LocalStorage(AbstractStorage):
    def __init__(self, root_path: Union[Path, AsyncPath]):
        self._root = (root_path if isinstance(root_path, AsyncPath) else AsyncPath(root_path)) / "storages"
        self._started = False

    async def start(self):
        if not self._started:
            await self._root.mkdir(exist_ok=True)
            self._started = True

    def close(self):
        pass

    async def stream_upload(self, key: str, key_id: str, filename: str, data: BytesIO, type: str = "images"):
        await self.start()
        path = self._root / type / key / key_id.replace("-", "") / filename
        await path.parent.mkdir(parents=True, exist_ok=True)
        data.seek(0)
        async with path.open("wb") as f:
            read = data.read(1024)
            if not read:
                return
            await f.write(read)

    async def stat_file(self, key: str, key_id: str, filename: str, type: str = "images"):
        await self.start()
        purepath = f"{type}/{key}/{key_id.replace('-', '')}/{filename}"
        path = self._root / type / key / key_id.replace("-", "") / filename
        try:
            stat_data = await path.stat()
            guess_mime, _ = guess_type(filename)
            guess_mime = guess_mime or "application/octet-stream"
            return FileObject(
                purepath,
                guess_mime,
                stat_data.st_size,
                pendulum.from_timestamp(stat_data.st_mtime),
            )
        except FileNotFoundError:
            return None

    async def exists(self, key: str, key_id: str, filename: str, type: str = "images"):
        await self.start()
        return await self.stat_file(key, key_id, filename, type) is not None

    async def stream_download(self, key: str, key_id: str, filename: str, type: str = "images"):
        await self.start()
        path = self._root / type / key / key_id.replace("-", "") / filename
        async with path.open("rb") as f:
            while True:
                chunk = await f.read(1024)
                if not chunk:
                    break
                yield chunk

    async def download(self, key: str, key_id: str, filename: str, type: str = "images"):
        await self.start()
        path = self._root / type / key / key_id.replace("-", "") / filename
        async with path.open("rb") as f:
            return await f.read()

    async def delete(self, key: str, key_id: str, filename: str, type: str = "images"):
        await self.start()
        path = self._root / type / key / key_id.replace("-", "") / filename
        await path.unlink(missing_ok=True)


_S3SESSION: S3BucketServer = None
_LOCALSERVER: LocalStorage = LocalStorage(AsyncPath(__file__).absolute().parent.parent.parent)


async def create_s3_server(hostname: str, access_key: str, secret_key: str, bucket_name: str):
    global _S3SESSION
    if _S3SESSION is not None:
        raise RuntimeError("S3 server already created")
    _S3SESSION = S3BucketServer(hostname, access_key, secret_key, bucket_name)
    await _S3SESSION.start()


def get_local_storage():
    return _LOCALSERVER


def get_s3_or_local():
    if _S3SESSION is None:
        return _LOCALSERVER
    return _S3SESSION
