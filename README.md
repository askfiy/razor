# Razor - A lightweight ASGI framework

## introduction

Razor is a lightweight ASGI (Asynchronous Server Gateway Interface) framework designed to simplify the construction and processing of web applications.

It provides a simple and flexible way to handle HTTP requests and build web applications while maintaining extensibility and customization.

## attribute

- Simple route management: Easily define and manage routes, map URLs to handlers.
- Middleware support: Extend and customize the request processing flow through middleware.
- ASGI compatible: Full support for the ASGI specification and can be used with ASGI servers such as uvicorn, Hypercorn, etc.
- Lightweight: Streamlined code base, reducing unnecessary complexity.
- Flexibility: Allows extensions to be customized according to project needs.

## use

Using Razor is fairly simple, and here's a short example:

```python
from razor import Application
from razor import TextResponse

app = Application()

@app.route("/index/")
async def index():
    return TextResponse("Hello Razor")

if __name__ == "__main__":
    app.run()
```

## document

To learn more about the Razor framework, see [Official documentation](https://github.com/askfiy/razor/wiki).

## contribution

If you find a bug, or have suggestions for improvement, please feel free to contribute code.

## license

The Razor Framework is licensed under the MIT license. For details, see [License File](https://github.com/askfiy/razor/blob/master/LICENSE).

## Acknowledgements

Thanks :

- [flask](https://github.com/pallets/flask)
- [quart](https://github.com/pallets/quart)
- [django](https://github.com/django/django)
- [asgi_tools](https://github.com/klen/asgi-tools)

Razor has learned a lot from you.
