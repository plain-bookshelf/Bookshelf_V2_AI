from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.v1.common.error.exception import BaseAppException

def exception_handler(app: FastAPI):
    @app.exception_handler(BaseAppException)
    async def app_exception_handler(request: Request, exc: BaseAppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )