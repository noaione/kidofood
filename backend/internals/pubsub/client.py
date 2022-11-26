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
import logging
from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional, Union

from ._types import PSAsyncCallback, PSCallback

__all__ = (
    "PubSubHandler",
    "get_pubsub",
)
PSDualCallback = Union[PSAsyncCallback, PSCallback]
logger = logging.getLogger("Internals.PubSub")


@dataclass
class PubSubTopic:
    type: Literal["iterator", "callback"]
    callback: Optional[PSDualCallback] = None


class PubSubHandler:
    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self.__topic_handler: Dict[str, PubSubTopic] = {}
        self._loop = loop or asyncio.get_event_loop()

        self._task_dict: Dict[str, asyncio.Task] = {}
        self._close_latch: bool = False

        self._msg_queue: Dict[str, asyncio.Queue[Any]] = {}

    async def close(self):
        self._close_latch = True
        for task in self._task_dict.values():
            task.cancel()
            await task

    # on done callback from create_task
    def _deregister_task(self, task: asyncio.Task) -> None:
        task_name = task.get_name()
        try:
            logger.info(f"Task {task_name} done, deregistering")
            del self._task_dict[task_name]
        except KeyError:
            pass

    async def _run_callback(self, callback: PSDualCallback, data: Any) -> None:
        logger.info(f"Running callback {callback!r} with data {data!r}")
        if asyncio.iscoroutinefunction(callback):
            await callback(data)
        else:
            await self._loop.run_in_executor(None, callback, data)

    def publish(self, topic: str, data: Any) -> None:
        if self._close_latch:
            logger.warning("PubSubHandler is closing, cannot publish")
            return
        if topic not in self.__topic_handler:
            return
        topical = self.__topic_handler[topic]
        logger.info(f"Publishing to {topic} with data {data!r}")
        if topical.type == "callback" and topical.callback is not None:
            task = asyncio.create_task(self._run_callback(topical.callback, data))
            task.add_done_callback(self._deregister_task)
            self._task_dict[task.get_name()] = task
        elif topical.type == "iterator":
            msg_q = self._msg_queue.get(topic)
            if msg_q is None:
                logger.warning(f"Topic {topic} is not subscribed to")
                return
            msg_q.put_nowait(data)

    def subscribe(self, topic: str, callback: PSDualCallback) -> None:
        self.__topic_handler[topic] = PubSubTopic(callback=callback, type="callback")

    def unsubscribe(self, topic: str) -> None:
        self.__topic_handler.pop(topic, None)

    async def listen(self, topic: str):
        self.__topic_handler[topic] = PubSubTopic(type="iterator")
        msg_q = self._msg_queue.get(topic) or asyncio.Queue[Any]()
        self._msg_queue[topic] = msg_q

        try:
            while True:
                try:
                    data = await asyncio.wait_for(msg_q.get(), timeout=10.0)
                    yield data
                except asyncio.TimeoutError:
                    if self._close_latch:
                        break
                    continue
        except asyncio.CancelledError:
            pass
        self.__topic_handler.pop(topic, None)
        self._msg_queue.pop(topic, None)


_GLOBAL_PUBSUB = PubSubHandler()


def get_pubsub():
    return _GLOBAL_PUBSUB
