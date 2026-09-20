import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connessione al DB (da implementare)
    yield
    # Shutdown: chiusura connessione

app = FastAPI(
    title="hikesmap API",
    version="0.1.0",
    # Swagger disabilitato in produzione
    docs_url=None if os.getenv("ENV") == "production" else "/docs",
    redoc_url=None if os.getenv("ENV") == "production" else "/redoc",
    lifespan=lifespan,
)

# CORS: accetta richieste solo dal frontend autorizzato
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173")
if not CORS_ORIGINS and os.getenv("ENV") == "production":
    raise RuntimeError("CORS_ORIGINS non configurato in produzione")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    """Controllo stato API — non espone dettagli interni."""
    return {"status": "ok"}

@app.get("/trails")
async def list_trails(
    bbox: str | None = None,
    difficulty: str | None = None,
    limit: int = 50,
):
    """
    Restituisce la lista dei sentieri.
    - bbox: bounding box geografico (minLon,minLat,maxLon,maxLat)
    - difficulty: T1..T6 (scala CAI)
    - limit: max risultati (default 50, max 200)
    """
    # TODO: query PostGIS
    limit = min(limit, 200)
    return {"trails": [], "total": 0, "limit": limit}
