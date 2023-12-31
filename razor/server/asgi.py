import functools
from typing import TYPE_CHECKING

from . import signals
from .logs import logger
from .response import Response, ErrorResponse, HTTPStatus
from .types import AsgiScope, AsgiReceive, AsgiSend, AsgiMessage
from .exceptions import NotFoundException, InvalidMethodException


if TYPE_CHECKING:
    from .application import Application


class AsgiLifespanHandle:
    """
    Manage the lifecycle of ASGI
    """

    def __init__(self, app: "Application"):
        self.app = app

    def _make_app_context(self):
        """
        Create a application context object
        """
        from .context import ApplicationContext
        return ApplicationContext(self.app)

    async def __call__(self, scope: AsgiScope, receive: AsgiReceive, send: AsgiSend):
        """
        ASGI creates an Asyncio Task for each request
        So the while loop here does not block the main coroutine
        """
        ctx = self._make_app_context()
        ctx.push()

        while True:
            message = await receive()
            # The application starts
            if message["type"] == "lifespan.startup":
                asgi_message = await self._callback_fn_("startup")
                await send(asgi_message)
            # The application closes
            elif message["type"] == "lifespan.shutdown":
                asgi_message = await self._callback_fn_("shutdown")
                await send(asgi_message)
                break

        ctx.pop()

    async def _callback_fn_(self, event: str) -> AsgiMessage:
        try:
            await self.app.event_manager.run_callback(event)
        except Exception as exc:
            return {"type": f"lifespan.{event}.failed", "message": str(exc)}
        return {"type": f"lifespan.{event}.complete"}


class AsgiHttpHandle:
    def __init__(self, app: "Application"):
        self.app = app

    def _make_req_context(self, scope: AsgiScope, receive: AsgiReceive, send: AsgiSend):
        """
        Create a request context object
        """
        from .context import RequestContext
        return RequestContext(scope, receive, send)

    async def _run_handler(self, handle):

        before_response = await self.app.event_manager.run_callback("before_request")
        if isinstance(before_response, Response):
            return before_response

        handle_response = await handle()

        if isinstance(handle_response, Response):

            callback_response = await self.app.event_manager.run_callback("after_request", handle_response)
            if isinstance(callback_response, Response):
                return callback_response
            return handle_response

        logger.error(
            f"Invalid response type, expecting `{Response.__name__}` but getting `{type(handle_response).__name__}`")

        return ErrorResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

    async def __call__(self, scope: AsgiScope, receive: AsgiReceive, send: AsgiSend):

        ctx = self._make_req_context(scope, receive, send)
        ctx.push()
        path, method = scope["path"], scope["method"]
        await signals.request_start.send_async(self.app)
        try:
            match = self.app.router(path, method)
            match.target.path_params = match.params or {}
            response = await self._run_handler(functools.partial(match.target, **match.target.path_params))
        except NotFoundException as exc:
            response = ErrorResponse(HTTPStatus.NOT_FOUND)
        except InvalidMethodException as exc:
            response = ErrorResponse(status_code=HTTPStatus.METHOD_NOT_ALLOWED)
        except Exception as exc:
            response = await self.app.event_manager.run_callback("exception", exc)
            # If a Type[Exception] is not returned, the exception is logged and handled by the framework itself
            if not isinstance(response, Response):
                logger.exception(exc)
                response = ErrorResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
        finally:
            await response(scope, receive, send)
            await signals.request_finish.send_async(self.app, response=response)
            # cleans up the context object
            ctx.pop()


class AsgiWebsocketHandle:
    def __init__(self, app: "Application"):
        self.app = app

    async def __call__(self, scope: AsgiScope, receive: AsgiReceive, send: AsgiSend):
        pass
