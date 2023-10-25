import re
import shutil
from typing import Any, Type, Optional, Union, Dict

from uvicorn import run as run_server

from .logs import LOGGING_CONFIG
from .router import Router
from .events import EventManager
from .types import AsgiScope, AsgiReceive, AsgiSend, RouterGroup
from .asgi import AsgiLifespanHandle, AsgiHttpHandle, AsgiWebsocketHandle


class Application:
    """
    Razor's main functional class

    ---
    from razor.server import Application, TextResponse

    app = Application(__name__)

    @app.route("/index/", methods=["GET", "POST"])
    async def index():
        return TextResponse("hello world")

    if __name__ == "__main__":
        app.run()
    ---
    """

    def __init__(self, name, trim_last_slash=False):
        """
        trim_last_slash : Whether the routing system is strictly matched
        """
        self.name = name
        self.event_manager = EventManager()
        self.router = Router(trim_last_slash)

        self.debug = False

    async def __call__(self, scope: AsgiScope, receive: AsgiReceive, send: AsgiSend):
        """
        Processing ASGI packets
        """
        if scope["type"] == "http":
            asgi_handler = AsgiHttpHandle(self)
        elif scope["type"] == "websocket":
            asgi_handler = AsgiWebsocketHandle(self)
        elif scope["type"] == "lifespan":
            asgi_handler = AsgiLifespanHandle(self)
        else:
            raise RuntimeError("ASGI Scope type is unknown")
        await asgi_handler(scope, receive, send)

    def route(self, *paths, methods=None, **opts):
        """
        Normal mode routing

        Simple route:
            - @app.route('/index')

        Dynamic route:
            - @app.route('/users/{username}')

        Converter route:
            - @app.route('/orders/{order_id:int}')

        Converter regex route:
            - @app.route('/orders/{order_id:\\d{3}}')

        Multiple path route:
            - @app.route('/doc', '/help')

        Class-Based View it will be processed automatically:
            - @app.route('/example')
              class Example:
                  ...
        """
        return self.router.route(*paths, methods=methods, **opts)

    def re_route(self, *paths, methods=None, **opts):
        """
        Regex mode routing

        @app.re_route('/regexp/\\w{3}-\\d{2}/?')
        """

        return self.route(
            *(re.compile(path) for path in paths),
            methods=methods,
            **opts
        )

    def add_routes(self, *routes):
        """
        Add routing relationship mappings in the normal way

          - app.add_routes(
                ("/help/", "/doc/", doc),      # fbv
                ("/test/", Example.as_view()), # cbv
            )
        """
        return self.router.add_routes(*routes)

    def on_event(self, event):
        """
        Register event callback
        ---
        # Available types
        from razor.events import EVENT_TYPE
        ---
        """
        def fn(callback):
            return self.event_manager.register(event, callback)
        return fn

    def on_startup(self, callback):
        """
        A startup callback function that registers lifespan

        @app.on_startup
        async def startup():
            ...
        """
        return self.event_manager.register("startup", callback)

    def on_shutdown(self, callback):
        """
        A shutdown callback function that registers lifespan

        @app.on_shutdown
        async def shutdown():
            ...
        """
        return self.event_manager.register("shutdown", callback)

    def on_before_request(self, callback):
        """
        Register a callback function when a request arrives

        @app.on_before_request
        async def before_request():
            ...
        """
        return self.event_manager.register("before_request", callback)

    def on_after_request(self, callback):
        """
        Register a callback function when a request leave

        @app.on_after_request
        async def after_request(resp) -> Response | None:
            ...
        """
        return self.event_manager.register("after_request", callback)

    def on_exception(self, callback):
        """
        Registers a callback function when user code runs an exception that is thrown
        HTTPStatus, such as 404, 405, etc. are not included

        @app.on_exception
        async def exception_handle(exc) -> Response | None:
            ...
        """
        return self.event_manager.register("exception", callback)

    def run(
        self,
        app: Optional[str | Type["Application"]] = None,
        host: str = "127.0.0.1",
        port: int = 5200,
        debug: bool = False,
        use_reloader: bool = True,
        ssl_ca_certs: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
        ssl_keyfile: Optional[str] = None,
        log_config: Optional[Union[Dict[str, Any], str]] = LOGGING_CONFIG,
        **kwargs: Any
    ):
        """
        Razor's startup function
        the specific parameters can be viewed in [uvicorn settings](https://www.uvicorn.org/settings/).
        """
        self.debug = debug
        app = app or self

        terminal_width, _ = shutil.get_terminal_size()
        stars = "-" * (terminal_width // 4)

        scheme = "https" if ssl_certfile is not None and ssl_keyfile is not None else "http"
        print(f"* Serving Razor app '{self.name}'")
        print(f"* Please use an ASGI server (e.g. Uvicorn) directly in production")
        print(f"* Debug mode: {self.debug or False}")
        print(f"* Running on \033[1m{scheme}://{host}:{port}\033[0m (CTRL + C to quit)")

        if not isinstance(app, str) and (use_reloader or kwargs.get("workers", 1) > 1):
            if not self.debug:
                print("* Not in debug mode. close auto reload")
            else:
                print("* You must pass the application as an import string to enable 'reload' or " "'workers'.")

            use_reloader = False

        print(stars)

        run_server(
            app,
            host=host,
            port=port,
            reload=use_reloader,
            ssl_certfile=ssl_certfile,
            ssl_keyfile=ssl_keyfile,
            ssl_ca_certs=ssl_ca_certs,
            log_config=log_config,
            **kwargs
        )
