import re
from io import BytesIO
from urllib.parse import unquote_to_bytes
from typing import Dict, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .request import Request

from multidict import MultiDict
from multipart.multipart import BaseParser, QuerystringParser, MultipartParser

from .datastructures import SpooledTemporaryFile


def unquote_plus(value: bytearray) -> bytes:
    value = value.replace(b"+", b" ")
    return unquote_to_bytes(bytes(value))


class FormDataReader:
    """
    Used to read data in a format other than multipart/form-data
    Such as application/x-www-form-urlencoded and other encoding formats
    """
    __slots__ = ("forms", "curkey", "curval", "charset", "files")

    def __init__(self, charset: str):
        self.forms = MultiDict()
        self.files = MultiDict()
        self.curkey = bytearray()
        self.curval = bytearray()
        self.charset = charset

    def on_field_name(self, data: bytes, start: int, end: int):
        # curkey is actually the final field name
        self.curkey += data[start:end]

    def on_field_data(self, data: bytes, start: int, end: int):
        # curval is actually the final field val
        self.curval += data[start:end]

    def on_field_end(self, *_):
        # converts bytearray to str and adds self.froms
        self.forms.add(
            unquote_plus(self.curkey).decode(self.charset),
            unquote_plus(self.curval).decode(self.charset),
        )
        self.curval.clear()
        self.curkey.clear()

    def get_parser(self, _: "Request") -> BaseParser:
        # parses the data through the QuerystringParser provided by the multipart module
        return QuerystringParser(
            {
                "on_field_name": self.on_field_name,
                "on_field_data": self.on_field_data,
                "on_field_end": self.on_field_end,
            },
        )


class MultipartReader:
    """
    Used to read data in multipart/form-data encoding format
    May contain information such as uploaded files
    """
    __slots__ = ("forms", "curkey", "curval", "charset", "filed_name", "headers", "filed_data", "files")

    def __init__(self, charset: str):
        self.forms = MultiDict()
        self.files = MultiDict()
        self.curkey = bytearray()
        self.curval = bytearray()
        self.charset = charset
        self.headers: Dict[bytes, bytes] = {}

        self.filed_name = ""
        self.filed_data = BytesIO()

    def get_parser(self, request: "Request") -> BaseParser:
        # For multipart/form-data type data, we should get the boundary from the content
        boundary = request.content.get("boundary", "")

        if not boundary:
            raise ValueError("Missing boundary")

        # parses the data through the MultipartParser provided by the multipart module
        return MultipartParser(
            boundary,
            {
                "on_header_field": self.on_header_field,
                "on_header_value": self.on_header_value,
                "on_header_end": self.on_header_end,
                "on_headers_finished": self.on_headers_finished,
                "on_part_data": self.on_part_data,
                "on_part_end": self.on_part_end,
            }
        )

    def on_header_field(self, data: bytes, start: int, end: int):
        # curkey is not the final field name
        self.curkey += data[start:end]

    def on_header_value(self, data: bytes, start: int, end: int):
        # curkey is not the final field value
        self.curval += data[start:end]

    def on_header_end(self, *_):
        # puts curkey and curval into self.headers
        self.headers[bytes(self.curkey.lower())] = bytes(self.curval)
        self.curkey.clear()
        self.curval.clear()

    def on_headers_finished(self, *_):
        _, options = parse_options_header(
            self.headers[b"content-disposition"].decode(self.charset),
        )


        self.filed_name = options["name"]

        if "filename" in options:
            # If the uploaded file is included, a temporary file is created to write the file data to memory
            self.filed_data = SpooledTemporaryFile()
            self.filed_data._file.name = options["filename"]
            self.filed_data.content_type = self.headers[b"content-type"].decode(self.charset)

    def on_part_data(self, data: bytes, start: int, end: int):
        # writes data to filed_data
        self.filed_data.write(data[start:end])

    def on_part_end(self, *_):
        field_data = self.filed_data

        # If it is data of a non-file type, add field_name and field_value to self.forms
        if isinstance(field_data, BytesIO):
            self.forms.add(self.filed_name, field_data.getvalue().decode(self.charset))
        else:
            # Otherwise, the file type data is added to self.files
            field_data.seek(0)
            self.files.add(self.filed_name, self.filed_data)

        self.filed_data = BytesIO()
        self.headers = {}


OPTION_HEADER_PIECE_RE = re.compile(
    r"""
    \s*,?\s*  # newlines were replaced with commas
    (?P<key>
        "[^"\\]*(?:\\.[^"\\]*)*"  # quoted string
    |
        [^\s;,=*]+  # token
    )
    (?:\*(?P<count>\d+))?  # *1, optional continuation index
    \s*
    (?:  # optionally followed by =value
        (?:  # equals sign, possibly with encoding
            \*\s*=\s*  # * indicates extended notation
            (?:  # optional encoding
                (?P<encoding>[^\s]+?)
                '(?P<language>[^\s]*?)'
            )?
        |
            =\s*  # basic notation
        )
        (?P<value>
            "[^"\\]*(?:\\.[^"\\]*)*"  # quoted string
        |
            [^;,]+  # token
        )?
    )?
    \s*;?
    """,
    flags=re.VERBOSE,
)


def parse_options_header(value: str) -> Tuple[str, Dict[str, str]]:
    """Parse the given content disposition header."""

    options: Dict[str, str] = {}
    if not value:
        return "", options

    if ";" not in value:
        return value, options

    ctype, rest = value.split(";", 1)
    while rest:
        match = OPTION_HEADER_PIECE_RE.match(rest)
        if not match:
            break

        option, count, encoding, _, value = match.groups()
        if value is not None:
            if encoding is not None:
                value = unquote_to_bytes(value).decode(encoding)

            if count:
                value = options.get(option, "") + value

        options[option] = value.strip('" ').replace("\\\\", "\\").replace('\\"', '"')
        rest = rest[match.end():]

    return ctype, options


async def parse_form_data(request: "Request") -> Tuple[MultiDict, MultiDict]:
    """
    A function provided to an external to parse form data from
    It gets the froms form data as well as a list of files
    """
    charset = request.content["charset"]
    content_type = request.content["content-type"]

    if content_type == "multipart/form-data":
        reader = MultipartReader(charset)
    else:
        reader = FormDataReader(charset)

    parser = reader.get_parser(request)

    parser.write(await request.body())
    parser.finalize()

    return reader.forms, reader.files
