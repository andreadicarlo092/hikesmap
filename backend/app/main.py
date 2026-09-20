import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.database import create_pool, close_pool, pool
from app.routers import trailheads, trails

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage asyncpg connection pool lifecycle."""
    logger.info("Starting up — creating DB pool…")
    await create_pool()
    logger.info("DB pool ready.")
    yield
    logger.info("Shutting down — closing DB pool…")
    await close_pool()
    logger.info("DB pool closed.")


app = FastAPI(
    title="Trail Explorer API",
    version="0.1.0",
    description="API REST per sentieri CAI — Trail Explorer",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────────────────────
app.include_router(trailheads.router, prefix=settings.API_PREFIX)
app.include_router(trails.router, prefix=settings.API_PREFIX)


# ── Core endpoints ───────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs", status_code=307)


@app.get(
    "/health",
    tags=["meta"],
    summary="Health check",
    response_description="Service and DB status",
)
async def health():
    """Returns service status and a quick DB connectivity check."""
    import app.database as db_module  # late import to pick up the live pool

    db_status = "error"
    if db_module.pool is not None:
        try:
            async with db_module.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            db_status = "ok"
        except Exception as exc:
            logger.warning("Health check DB probe failed: %s", exc)

    return {"status": "ok", "db": db_status}


# ── Global exception handlers ─────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.info("Validation error on %s: %s", request.url, exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s: %s", request.url, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
