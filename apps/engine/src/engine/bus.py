"""Tiny async event bus. Every event is also kept in memory and persisted by the store."""
from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

Handler = Callable[[dict[str, Any]], Awaitable[None] | None]


class EventBus:
    def __init__(self, history: int = 1000) -> None:
        self._handlers: list[Handler] = []
        self._queues: set[asyncio.Queue] = set()
        self.history: deque[dict[str, Any]] = deque(maxlen=history)

    def subscribe(self, handler: Handler) -> None:
        self._handlers.append(handler)

    def listen(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=500)
        self._queues.add(q)
        return q

    def unlisten(self, q: asyncio.Queue) -> None:
        self._queues.discard(q)

    async def emit(self, event: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        item = {
            "event": event,
            "time": datetime.now(timezone.utc).isoformat(),
            "data": data or {},
        }
        self.history.append(item)
        for h in self._handlers:
            res = h(item)
            if asyncio.iscoroutine(res):
                await res
        for q in list(self._queues):
            if q.full():
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            q.put_nowait(item)
        return item
