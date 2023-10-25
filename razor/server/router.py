import inspect
from typing import Optional, ClassVar, Type, Tuple, Callable, TYPE_CHECKING

from http_router import Router as HttpRouter

from .exceptions import RouterException, NotFoundException, InvalidMethodException
from .views import View


if TYPE_CHECKING:
    from http_router.types import TVObj, TPath, TMethodsArg


class Router(HttpRouter):
    RouterError: ClassVar[Type[Exception]] = RouterException
    NotFoundError: ClassVar[Type[Exception]] = NotFoundException
    InvalidMethodError: ClassVar[Type[Exception]] = InvalidMethodException

    def route(
        self,
        *paths: "TPath",
        methods: Optional["TMethodsArg"] = None,
        **opts,
    ) -> Callable[["TVObj"], "TVObj"]:
        """Register a route."""

        def wrapper(target: "TVObj") -> "TVObj":
            nonlocal methods
            """
            Overrides the wrapper method to support CBV views
            """
            if inspect.isclass(target) and issubclass(target, View):
                target = target.as_view()
            else:
                methods = methods or ["GET"]
                if "OPTIONS" not in methods:
                    methods.append("OPTIONS")

            if hasattr(target, "__route__"):
                target.__route__(self, *paths, methods=methods, **opts)
                return target

            if not self.validator(target):
                raise self.RouterError("Invalid target: %r" % target)

            target = self.converter(target)
            self.bind(target, *paths, methods=methods, **opts)
            return target

        return wrapper

    def add_routes(self, *routes):
        """
        Add routes should support all methods for FBV, so super's route method is called here
        """
        for route_rule in routes:
            *paths, handle = route_rule
            super().route(*paths)(handle)
