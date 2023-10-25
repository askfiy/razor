class RegisterEventException(Exception):
    pass


class RouterException(Exception):
    pass


class NotFoundException(RouterException):
    pass


class InvalidMethodException(RouterException):
    pass
