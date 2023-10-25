"""
Razor is a fast ASGI-based http framework that tries to entice you with the most concise speed

Thanks to the following open source frameworks, Razor has learned a lot from you:

- [flask](https://github.com/pallets/flask)
- [quart](https://github.com/pallets/quart)
- [asgi_tools](https://github.com/klen/asgi-tools)
- [django](https://github.com/django/django)
"""

from .application import Application

from .globals import (
    request,
    current_application
)

from .response import (
    Response,
    TextResponse,
    HtmlResponse,
    JsonResponse,
    RedirectResponse,
    ErrorResponse
)

from .views import View
