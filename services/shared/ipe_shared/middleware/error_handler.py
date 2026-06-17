import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ipe_shared.exceptions import IPEError

logger = logging.getLogger("ipe.error")


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(IPEError)
    async def ipe_error_handler(request: Request, exc: IPEError):
        logger.warning("IPE error: %s - %s", exc.code, exc.message)
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception: %s", str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                },
            },
        )
