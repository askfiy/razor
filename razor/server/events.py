from typing import Dict, List, Awaitable, Any
from .response import Response
from .exceptions import RegisterEventException


class AbstractEvent:
    def __call__(self, callback_result, event):
        if callback_result is not None:
            raise TypeError(f"event '{event}' callback result is not None")


class StartupEvent(AbstractEvent):
    pass


class ShutdownEvent(AbstractEvent):
    pass


class AfterRequestEvent(AbstractEvent):
    def __call__(self, callback_result, event):
        if not isinstance(callback_result, Response):
            raise TypeError(f"event '{event}' callback result is not {Response.__class__.__name__}")
        return callback_result


class BeforeRequestEvent(AbstractEvent):
    def __call__(self, callback_result, event):
        if (callback_result is not None) and (not isinstance(callback_result, Response)):
            raise TypeError(f"event '{event}' callback result is not {Response.__class__.__name__} or None")
        return callback_result


class ExceptionEvent(AbstractEvent):
    def __call__(self, callback_result, event):
        if not (isinstance(callback_result, Exception) or isinstance(callback_result, Response)):
            raise TypeError(f"event '{event}' callback result is not {Response.__class__.__name__} or Exception")
        return callback_result


class EventManager:
    """
    An event manager object that provides functionality such as registering events and running callbacks
    """

    SUPPORT_EVENT = {
        "startup": StartupEvent(),
        "shutdown": ShutdownEvent(),
        "after_request": AfterRequestEvent(),
        "before_request": BeforeRequestEvent(),
        "exception": ExceptionEvent()
    }

    def __init__(self):
        self._events: Dict[str, List[Awaitable[Any, Any]]] = {
            k: []
            for k in self.SUPPORT_EVENT.keys()
        }

    def register(self, event: str, callback):
        if event not in self.SUPPORT_EVENT.keys():
            raise RegisterEventException(f"registering an `{event}` failed, event is not exists")
        self._events[event].append(callback)

    async def run_callback(self, event, *args, **kwargs):
        callbacks = self._events.get(event)
        callback_type_ins = self.SUPPORT_EVENT[event]

        for callback in callbacks:
            cb_r = callback_type_ins(await callback(*args, **kwargs), event)
            if cb_r is not None:
                args = (cb_r, )
        if args:
            return args[0]
