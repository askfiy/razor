from contextvars import ContextVar

from .proxy import LocalProxy
from .request import Request
from .application import Application


_cv_request: ContextVar = ContextVar("razor.request_context")
_cv_application: ContextVar = ContextVar("razor.application_context")

request: Request = LocalProxy(_cv_request, Request)
current_application: Application = LocalProxy(_cv_application, Application)
