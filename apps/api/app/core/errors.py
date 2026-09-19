"""Uniform error envelope `{"error": {"code", "message"[, "details"]}}` (TZ §4.6)."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

log = logging.getLogger("neuroai.errors")


class AppError(Exception):
    """Domain error with a stable machine-readable code; subclass or pass code/status."""

    status_code: int = 400
    code: str = "app_error"

    def __init__(
        self, message: str, *, code: str | None = None, status_code: int | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


def error_response(
    status_code: int,
    code: str,
    message: str,
    *,
    details: Any = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    error: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return JSONResponse(status_code=status_code, content={"error": error}, headers=headers)


def internal_error_response() -> JSONResponse:
    # Never expose internals to the client.
    return error_response(500, "internal_error", "Ichki xatolik yuz berdi")


class UnhandledErrorMiddleware:
    """Pure ASGI: turns an uncaught exception into the 500 envelope *inside* CORS/RequestId.

    Starlette's own catch-all (ServerErrorMiddleware) runs outside every user middleware, so a
    500 built there carries neither CORS nor X-Request-ID headers. This must therefore be the
    innermost user middleware: `create_app()` registers it first (add_middleware prepends).
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            log.exception("unhandled error", extra={"path": scope["path"]})
            if response_started:
                raise  # too late to replace the response; ServerErrorMiddleware takes over
            await internal_error_response()(scope, receive, send)


async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return error_response(exc.status_code, exc.code, exc.message)


async def _http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        code, message = str(detail["code"]), str(detail.get("message", ""))
    else:
        code, message = f"http_{exc.status_code}", str(detail)
    return error_response(exc.status_code, code, message, headers=exc.headers)


async def _validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(
        422,
        "validation_error",
        "So'rov ma'lumotlari noto'g'ri",
        details=jsonable_encoder(exc.errors()),
    )


async def _unhandled_handler(_: Request, __: Exception) -> JSONResponse:
    # Last resort (ServerErrorMiddleware), only for errors that escape UnhandledErrorMiddleware.
    return internal_error_response()


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _validation_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _unhandled_handler)
