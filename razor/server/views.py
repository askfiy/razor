class View:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def as_view(cls, **initkwargs):
        async def view(*args, **kwargs):
            self = cls(**initkwargs)
            self.setup(*args, **kwargs)
            return await self.dispatch(*args, **kwargs)

        view.view_class = cls
        view.view_initkwargs = initkwargs

        view.__doc__ = cls.__doc__
        view.__module__ = cls.__module__
        view.__annotations__ = cls.dispatch.__annotations__
        view.__dict__.update(cls.dispatch.__dict__)

        return view

    async def dispatch(self, *args, **kwargs):

        from .globals import request
        from .response import ErrorResponse, HTTPStatus

        if hasattr(self, request.method.lower()):
            handler = getattr(self, request.method.lower())
            return await handler(*args, **kwargs)

        return ErrorResponse(HTTPStatus.METHOD_NOT_ALLOWED)

    def setup(self, *args, **kwargs):
        if hasattr(self, "get") and not hasattr(self, "head"):
            self.head = self.get
