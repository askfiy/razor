from typing import Dict, List, Awaitable, Any
from .exceptions import RegisterEventException

# currently supports internal event types
EVENT_TYPE = (
    # lifespan event
    "startup",
    "shutdown",
    # http event
    "after_request",
    "before_request",
    # exception event
    "exception"
)


class EventManager:
    """
    An event manager object that provides functionality such as registering events and running callbacks
    """

    def __init__(self):
        self._events: Dict[str, List[Awaitable[Any, Any]]] = {
            k: []
            for k in EVENT_TYPE
        }

    def register(self, event: str, callback):
        if event not in EVENT_TYPE:
            raise RegisterEventException(f"registering an `{event}` failed, event is not exists")
        self._events[event].append(callback)

    async def run_callback(self, event, *args, **kwargs):
        callbacks = self._events.get(event)
        for callback in callbacks:
            cb_r = await callback(*args, **kwargs)
            if cb_r is not None:
                args = (cb_r, )
        if args:
            return args[0]
