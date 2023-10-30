import json
from http import HTTPStatus
from http.cookies import SimpleCookie
from typing import Optional
from urllib.parse import quote_plus

from multidict import MultiDict
from markupsafe import escape

from .types import AsgiScope, AsgiReceive, AsgiSend
from .constants import DEFAULT_CODING, DEFAULT_CHARSET


class Response:
    status_code: int = HTTPStatus.OK.value
    content_type: Optional[str] = None

    def __init__(self, content, *, status_code=200, content_type=None, headers=None, cookies=None) -> None:
        self.status_code = status_code
        self.cookies = SimpleCookie(cookies)
        self.headers = MultiDict(headers or {})
        self.content = self.handle_content(content)

        content_type = content_type or self.content_type
        if content_type:
            if content_type.startswith("text/"):
                content_type = "{}; charset={}".format(content_type, DEFAULT_CODING)

            self.headers.setdefault("content-type", content_type)

    def handle_content(self, content):

        if not isinstance(content, bytes):
            return str(content).encode(DEFAULT_CODING)

        return content

    async def __call__(self, scope: AsgiScope, receive: AsgiReceive, send: AsgiSend) -> None:
        self.headers.setdefault("content-length", str(len(self.content)))

        headers = [
            (key.encode(DEFAULT_CHARSET), str(val).encode(DEFAULT_CHARSET))
            for key, val in self.headers.items()
        ]

        for cookie in self.cookies.values():
            headers = [
                *headers,
                (b"set-cookie", cookie.output(header="").strip().encode(DEFAULT_CHARSET)),
            ]

        await send({
            "type": "http.response.start",
            "status": self.status_code,
            "headers": headers,
        })

        await send({"type": "http.response.body", "body": self.content})

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.status_code}>"


class TextResponse(Response):
    content_type = "text/plain"


class HtmlResponse(Response):
    content_type = "text/html"


class JsonResponse(Response):
    content_type = "application/json"

    def handle_content(self, content):
        return json.dumps(content, ensure_ascii=False).encode("utf-8")


class RedirectResponse(Response):
    status_code: int = HTTPStatus.TEMPORARY_REDIRECT.value

    def __init__(self, url, status_code: Optional[int] = None, **kwargs) -> None:

        self.status_code = status_code or self.status_code

        super().__init__(
            content=b"",
            status_code=self.status_code,
            **kwargs
        )

        assert 300 <= self.status_code < 400, f"Invalid status code for redirection: {self.status_code}"

        self.headers["location"] = quote_plus(url, safe=":/%#?&=@[]!$&'()*+,;")


class ErrorResponse(Response):
    content_type = "text/html"

    def __init__(self, status_code: int, content=None, **kwargs):
        if status_code < 400:
            raise ValueError("response code < 400")

        _o = HTTPStatus(status_code)
        content = content or self.get_err_page(_o.value, _o.phrase, _o.description)

        super().__init__(
            content=content,
            status_code=status_code,
            **kwargs
        )

    def get_err_page(self, code, name, descript):
        return (
            "<!doctype html>\n"
            "<html lang=en>\n"
            f"<title>{code} {escape(name)}</title>\n"
            f"<h1>{escape(name)}</h1>\n"
            f"<p>{escape(descript)}</p>\n"
        )
