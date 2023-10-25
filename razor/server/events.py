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
        self._events = {}

    def register(self, event: str, callback):
        if event not in EVENT_TYPE:
            raise RegisterEventException(f"registering an `{event}` failed, event is not exists")

        if event in self._events:
            raise RegisterEventException(f"registering an `{event}` failed, callback is registered")
        self._events[event] = callback

    async def run_callback(self, event, *args, **kwargs):
        callback = self._events.get(event)
        if callback:
            return await callback(*args, **kwargs)
