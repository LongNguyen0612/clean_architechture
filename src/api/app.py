from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from .error import ClientError, ServerError
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
import sentry_sdk
from src.api.routes.health_check import router as health_check_router
from src.api.routes.user import router as user_router
logger = logging.getLogger(__name__)


def setup_sentry(config):
    sentry_sdk.init(
        dsn=config.DSN_SENTRY,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        enable_tracing=True,
        traces_sample_rate=1.0,
        environment=config.SENTRY_ENVIRONMENT,
    )


async def get_request_info(request: Request):
    headers = dict(request.headers)
    headers.pop("cookie", None)
    headers.pop("authorization", None)
    headers.pop("x-api-key", None)
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        raw_body = await request.body()
        body = raw_body.decode("utf-8")

    return {
        "method": request.method,
        "url": request.url,
        "client": request.client.host,
        "headers": headers,
        "query_params": dict(request.query_params),
        "body": body,
    }

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Request: {request.method} {request.url.path} {request.client.host}")
        t = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - t) * 1000
        logger.info(
            "Finished request %s %s. Status code: %s. Duration in ms: %s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response



async def handle_unexpected_error(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"},
    )


async def handle_client_error(request: Request, exc: ClientError):
    request_info = await get_request_info(request)
    logger.warning(
        f"Client error: {exc.to_dict()}. Reason: {exc.get_reason()}. Request: {request_info}"
    )
    return JSONResponse(
        status_code=exc.get_status_code(),
        content={"error": exc.to_dict()},
    )


async def handle_server_error(request: Request, exc: ServerError):
    request_info = await get_request_info(request)
    logger.warning(
        f"Server error: {exc.to_dict()}. Reason: {exc.get_reason()}. Request: {request_info}"
    )
    logger.error(f"Server error: {exc.to_dict()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": exc.to_dict()},
    )



def create_app(ApplicationConfig) -> FastAPI:
    if ApplicationConfig.ENABLE_SENTRY:
        setup_sentry(ApplicationConfig)
    app = FastAPI(
        title="Backend API",
        description="API for the Backend Template application",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    if ApplicationConfig.ENABLE_LOGGING_MIDDLEWARE:
        app.add_middleware(LoggingMiddleware)
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ApplicationConfig.CORS_ORIGINS,
        allow_credentials=ApplicationConfig.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Configure routing
    api_prefix = ApplicationConfig.API_PREFIX
    app.include_router(
        health_check_router,
        tags=["Health Check"],
    )
    app.include_router(
        user_router,
        tags=["User"],
    )

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    # Configure error handlers
    app.add_exception_handler(ClientError, handle_client_error)
    app.add_exception_handler(ServerError, handle_server_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
    return app
