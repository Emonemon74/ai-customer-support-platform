import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.documents import router as documents_router
from app.api.v1.health import router as health_router
from app.api.v1.users import router as users_router
from app.core.exceptions.handlers import register_exception_handlers
from app.core.logging.logger import logger
from app.core.observability import (
    bind_context,
    configure_logging,
    metrics,
    new_request_id,
    set_context,
)
from app.core.settings import settings

configure_logging()

# Sent on every response. The API serves JSON only and is never framed.
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or new_request_id()
    bind_context(request_id=request_id)

    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        metrics.inc("http_requests_total", method=request.method, status="500")
        metrics.inc("http_request_errors_total", method=request.method)
        logger.exception(
            "request failed %s %s (%.1f ms)",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)

    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)
    metrics.inc("http_requests_total", method=request.method, status=str(response.status_code))
    metrics.observe("http_request_duration_ms", duration_ms, method=request.method)
    if response.status_code >= 500:
        metrics.inc("http_request_errors_total", method=request.method)

    logger.info(
        "%s %s -> %s (%.1f ms)",
        request.method,
        path,
        response.status_code,
        duration_ms,
    )
    return response


register_exception_handlers(app)


@app.get("/metrics", response_class=PlainTextResponse, tags=["Health"])
def metrics_endpoint() -> str:
    return metrics.render()


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(conversations_router)


# Re-exported for callers that set request-scoped ids.
__all__ = ["app", "set_context"]
