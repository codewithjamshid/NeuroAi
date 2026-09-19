"""Error shape {"error": {"code", "message"}} for every non-2xx response (TZ §4.6)."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

_HTTP_CODES = {401: "unauthorized", 403: "forbidden", 404: "not_found", 405: "method_not_allowed"}


class WorkerError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class ModelNotLoaded(WorkerError):
    def __init__(self, model: str) -> None:
        super().__init__(
            503, "model_not_loaded", f"{model} model not loaded — see docs/AI_WORKER_TZ.md"
        )


class ModelUnavailable(RuntimeError):
    """Raised by <module>.load() when the model/library is not available on this machine."""


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"error": {"code": code, "message": message}}
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(WorkerError)
    async def _worker_error(_: Request, exc: WorkerError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _HTTP_CODES.get(exc.status_code, "http_error")
        return error_response(exc.status_code, code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        loc = ".".join(str(p) for p in first.get("loc", ()))
        msg = f"{loc}: {first.get('msg', 'invalid request')}" if loc else "invalid request"
        return error_response(422, "validation_error", msg)
