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
from typing import Any, Dict, Optional, Union

from ._types import PSCallback, PSAsyncCallback

__all__ = ("PubSubHandler",)
PSDualCallback = Union[PSAsyncCallback, PSCallback]


class PubSubHandler:
    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self.__topic_handler: Dict[str, PSDualCallback] = {}
        self._loop = loop or asyncio.get_event_loop()

        self._task_dict: Dict[str, asyncio.Task] = {}

    # on done callback from create_task
    def _deregister_task(self, task: asyncio.Task) -> None:
        task_name = task.get_name()
        try:
            del self._task_dict[task_name]
        except KeyError:
            pass

    async def _run_callback(self, callback: PSDualCallback, data: Any) -> None:
        if asyncio.iscoroutinefunction(callback):
            await callback(data)
        else:
            await self._loop.run_in_executor(None, callback, data)

    def publish(self, topic: str, data: Any) -> None:
        if topic not in self.__topic_handler:
            return
        callback = self.__topic_handler[topic]
        task = asyncio.create_task(self._run_callback(callback, data))
        task.add_done_callback(self._deregister_task)
        self._task_dict[task.get_name()] = task

    def subscribe(self, topic: str, callback: PSDualCallback) -> None:
        self.__topic_handler[topic] = callback

    def unsubscribe(self, topic: str) -> None:
        self.__topic_handler.pop(topic, None)
