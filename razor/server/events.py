from typing import Dict, List, Awaitable, Any
from .response import Response
from .exceptions import RegisterEventException


class EventResponseHandler:
    def __call__(self, event, cb_resp):
        return getattr(self, f"__{event}__")(event, cb_resp)

    def __startup__(self, event, cb_resp):
        if cb_resp is not None:
            raise TypeError(f"event '{event}' callback result is not None")

    def __shutdown__(self, event, cb_resp):
        if cb_resp is not None:
            raise TypeError(f"event '{event}' callback result is not None")

    def __after_request__(self, event, cb_resp):
        if not isinstance(cb_resp, Response):
            raise TypeError(f"event '{event}' callback result is not {Response.__class__.__name__}")
        return cb_resp

    def __before_request__(self, event, cb_resp):
        if (cb_resp is not None) and (not isinstance(cb_resp, Response)):
            raise TypeError(f"event '{event}' callback result is not {Response.__class__.__name__} or None")
        return cb_resp

    def __exception__(self, event, cb_resp):
        if not (isinstance(cb_resp, Exception) or isinstance(cb_resp, Response)):
            raise TypeError(f"event '{event}' callback result is not {Response.__class__.__name__} or Exception")
        return cb_resp


class EventManager:
    """
    An event manager object that provides functionality such as registering events and running callbacks
    """

    EVENT_TYPES = (
        "startup",
        "shutdown",
        "after_request",
        "before_request",
        "exception"
    )

    def __init__(self):
        self._events: Dict[str, List[Awaitable[Any, Any]]] = {
            event: []
            for event in self.EVENT_TYPES
        }
        self._event_resp_handle = EventResponseHandler()

    def register(self, event: str, callback):
        if event not in self.EVENT_TYPES:
            raise RegisterEventException(f"registering an `{event}` failed, event is not exists")
        self._events[event].append(callback)

    async def run_callback(self, event, *args, **kwargs):
        callbacks = self._events.get(event)

        for callback in callbacks:
            cb_r = self._event_resp_handle(event, await callback(*args, **kwargs))
            if cb_r is not None:
                args = (cb_r, )
        if args:
            return args[0]
