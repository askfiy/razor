import json
from http.cookies import _unquote
from typing import Any, Union, Optional

from multidict import MultiDict

from .constants import DEFAULT_CODING, DEFAULT_CHARSET
from .forms import parse_form_data, SpooledTemporaryFile
from .types import AsgiScope, AsgiReceive, AsgiSend, AsgiMessage, JsonMapping


class Request:

    __slots__ = (
        "scope",
        "receive",
        "send",
        "_headers",
        "_cookies",
        "_query",
        "_content",
        "_body",
        "_text",
        "_forms",
        "_files",
        "_json"
    )

    def __init__(self, scope: AsgiScope, receive: AsgiReceive, send: AsgiSend):
        self.scope = scope
        self.receive = receive
        self.send = send

        self._content: Optional[MultiDict[str]] = None
        self._headers: Optional[MultiDict[str]] = None
        self._cookies: Optional[MultiDict[str]] = None
        self._query: Optional[MultiDict[str]] = None
        self._body: Optional[bytes] = None
        self._text: Optional[str] = None
        self._json: Optional[JsonMapping] = None
        self._forms: Optional[MultiDict[str]] = None
        self._files: Optional[MultiDict[SpooledTemporaryFile]] = None

    def __getitem__(self, key: str) -> Any:
        return self.scope[key]

    def __getattr__(self, key) -> Any:
        return self.scope[key]

    @property
    def content(self) -> MultiDict:
        """The cache lazy parses data in content-type"""
        if not self._content:
            self._content = MultiDict()
            content_type, *parameters = self.headers.get("content-type", "").split(";", 1)
            for parameter in parameters:
                key, value = parameter.strip().split("=", 1)
                self._content.add(key, value)
            self._content.add("content-type", content_type)
            self._content.setdefault("charset", DEFAULT_CODING)
        return self._content

    @property
    def headers(self) -> MultiDict:
        """Cache lazy parse data in headers"""
        if not self._headers:
            self._headers = MultiDict()
            for key, val in self.scope["headers"]:
                self._headers.add(key.decode(DEFAULT_CHARSET), val.decode(DEFAULT_CHARSET))
            self._headers["remote-addr"] = (self.scope.get("client") or ["<local>"])[0]
        return self._headers

    @property
    def cookies(self) -> MultiDict:
        """Cache lazy parses data in cookies"""
        if not self._cookies:
            self._cookies = MultiDict()
            for chunk in self.headers.get("cookie").split(";"):
                key, _, val = chunk.partition("=")
                if key and val:
                    self._cookies[key.strip()] = _unquote(val.strip())
        return self._cookies

    @property
    def query(self) -> MultiDict:
        """Cache query parameters in lazy resolution URLs"""
        if not self._query:
            self._query = MultiDict()
            for chunk in self.scope["query_string"].decode(DEFAULT_CHARSET).split("&"):
                key, _, val = chunk.partition("=")
                if key and val:
                    self._query.add(key.strip(), val.strip())
        return self._query

    async def body(self) -> bytes:
        """Cache lazy parsing request body"""
        if not self._body:
            self._body: bytes = b""
            while True:
                message: AsgiMessage = await self.receive()
                self._body += message.get("body", b"")
                if not message.get("more_body"):
                    break
        return self._body

    async def text(self) -> str:
        """An attempt was made to transcode and return the request body data"""
        if not self._text:
            body = await self.body()
            self._text = body.decode(self.content["charset"])
        return self._text

    async def form(self) -> MultiDict:
        """The cache lazy loads data from the form"""
        if not self._forms:
            self._forms, self._files = await parse_form_data(self)
        return self._forms

    async def files(self) -> MultiDict[SpooledTemporaryFile]:
        """Cache lazy loading from files uploaded in the form"""
        if not self._files:
            self._forms, self._files = await parse_form_data(self)
        return self._files

    async def json(self) -> JsonMapping:
        """An attempt was made to deserialize and return the request body data in JSON format"""
        if not self._json:
            text = await self.text()
            self._json = json.loads(text) if text else {}
        return self._json

    async def data(self) -> Union[MultiDict, JsonMapping, str]:
        """Get different results depending on the type of request"""
        content_type = self.content["content-type"]
        if content_type == "application/json":
            return await self.json()
        if content_type == "multipart/form-data":
            return await self.form()
        if content_type == "application/x-www-form-urlencoded":
            return await self.form()
        return self.text()
