import contextvars
from typing import Any, List, Type, TYPE_CHECKING

from .request import Request
from .types import AsgiScope, AsgiReceive, AsgiSend
from .globals import _cv_request, _cv_application

if TYPE_CHECKING:
    from .application import Application


class Context:
    """
    Basic context class
    """

    def __init__(self, ctx_var: contextvars.ContextVar, var: Any) -> None:
        self._var = var
        self._ctx_var = ctx_var
        self._cv_tokens: List[contextvars.Token] = []

    def push(self) -> None:
        # records the token of the context variable
        # Pushes the token into the list
        self._cv_tokens.append(
            self._ctx_var.set(self._var)
        )

    def pop(self) -> None:
        # Resets the context variable if the length of the token list is 1
        if len(self._cv_tokens) == 1:
            token = self._cv_tokens.pop()
            self._ctx_var.reset(token)


class ApplicationContext(Context):
    """
    App context
    """

    def __init__(self, app):
        self._app = app
        super().__init__(
            ctx_var=_cv_application,
            var=self._app
        )


class RequestContext(Context):
    """
    Request context
    """

    def __init__(self, scope: AsgiScope, receive: AsgiReceive, send: AsgiSend):
        self._request = Request(scope, receive, send)
        super().__init__(
            ctx_var=_cv_request,
            var=self._request
        )

