import os
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.database import connect, disconnect, get_pool
from api.models import TrailList

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect()
    yield
    await disconnect()

app = FastAPI(
    title="hikesmap API",
    version="0.1.0",
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


@app.get("/trails", response_model=TrailList)
async def list_trails(
    bbox: str | None = Query(None, description="minLon,minLat,maxLon,maxLat"),
    difficulty: str | None = Query(None, description="T1..T6 scala CAI"),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Restituisce la lista dei sentieri filtrati per area geografica e difficoltà.
    """
    pool = get_pool()

    # Costruzione query con parametri (mai interpolazione diretta — SQL injection)
    conditions = []
    params = []

    if bbox:
        parts = bbox.split(",")
        if len(parts) != 4:
            raise HTTPException(status_code=400, detail="bbox deve essere minLon,minLat,maxLon,maxLat")
        try:
            min_lon, min_lat, max_lon, max_lat = [float(p) for p in parts]
        except ValueError:
            raise HTTPException(status_code=400, detail="bbox contiene valori non numerici")
        params += [min_lon, min_lat, max_lon, max_lat]
        conditions.append(
            f"ST_Intersects(geometry, ST_MakeEnvelope(${len(params)-3}, ${len(params)-2}, ${len(params)-1}, ${len(params)}, 4326))"
        )

    if difficulty:
        params.append(difficulty)
        conditions.append(f"difficulty = ${len(params)}")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(limit)

    # TODO: aggiungere SELECT completo con tutti i campi del modello Trail
    rows = await pool.fetch(
        f"SELECT id, osm_id, name, ref, difficulty FROM trails {where} LIMIT ${len(params)}",
        *params
    )

    return TrailList(
        trails=[dict(r) for r in rows],
        total=len(rows),
        limit=limit,
    )
