from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.logger import log


class AppError(Exception):
    """An error we expect, with the HTTP status we want to send back."""

    def __init__(self, status_code, code, message):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def error_body(code, message, details=None):
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return body


def add_error_handlers(app):
    @app.exception_handler(AppError)
    async def app_error(request: Request, error: AppError):
        return JSONResponse(error_body(error.code, error.message), status_code=error.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        details = [
            {"field": ".".join(str(part) for part in e["loc"][1:]) or "request", "message": e["msg"]}
            for e in error.errors()
        ]
        return JSONResponse(
            error_body("validation_error", "Invalid request.", details), status_code=422
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, error: Exception):
        log("unhandled_error", level=40, error=repr(error))
        return JSONResponse(error_body("internal_error", "Something went wrong."), status_code=500)
