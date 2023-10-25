from typing import (
    TypedDict,
    List,
    Tuple,
    Callable,
    Mapping,
    Any,
    Awaitable,
    Type,
    Union
)

from .views import View


AsgiHeaders = List[Tuple[bytes, bytes]]


class _AsgiScopeAsgi(TypedDict):
    version: str
    spec_version: str


class AsgiScope(TypedDict):
    type: str
    asgi: _AsgiScopeAsgi
    http_version: str
    server: Tuple[str, int]
    client: Tuple[str, int]
    scheme: str
    method: str
    root_path: str
    path: str
    raw_path: bytes
    query_string: bytes
    headers: AsgiHeaders
    state: Mapping[str, Any]


AsgiMessage = Mapping[str, Any]
AsgiReceive = Callable[[], Awaitable[AsgiMessage]]
AsgiSend = Callable[[AsgiMessage], Awaitable[None]]

JsonMapping = Mapping[str, Any]

RouterGroup = Tuple[Union[str, Tuple[str, ...]], Type[View]]
