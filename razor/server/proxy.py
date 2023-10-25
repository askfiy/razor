import operator
from functools import partial
from contextvars import ContextVar


class _ProxyLookup:
    def __init__(self, f):
        def bind_f(instance: "LocalProxy", obj):
            return partial(f, obj)
        self.bind_f = bind_f

    def __get__(self, instance: "LocalProxy", owner: type | None = None):
        obj = instance._get_current_object()
        return self.bind_f(instance, obj)

    def __call__(self, instance: "LocalProxy", *args, **kwargs):
        return self.__get__(instance, type(instance))(*args, **kwargs)


class LocalProxy:
    def __init__(self, local, proxy):
        self.local = local
        self.proxy = proxy

    def _get_current_object(self):
        if isinstance(self.local, ContextVar):
            return self.local.get()
        raise RuntimeError(f"Unsupported local type:{type(self.local)}")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.proxy.__module__}.{self.proxy.__name__}>"

    __getattr__ = _ProxyLookup(getattr)
    __getitem__ = _ProxyLookup(operator.__getitem__)
