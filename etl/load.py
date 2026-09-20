"""
etl/load.py — Carica i dati estratti in PostgreSQL/PostGIS.

Flusso:
  1. Connessione al DB tramite asyncpg (credenziali da .env, mai hardcoded)
  2. UPSERT dei trail via osm_id (idempotente: sicuro da rieseguire)
  3. UPSERT di shelters, water_sources, parkings
  4. Calcolo e inserimento nelle join table (trail_shelters, ecc.)
     con distanza in metri tramite PostGIS ST_Distance
  5. Ogni operazione usa query parametrizzate — mai interpolazione di stringa

Sicurezza:
  - Usa l'utente hikesmap_etl (solo INSERT/UPDATE, non DROP/DELETE)
  - Nessuna credenziale nei log
  - Transazione per-record: un sentiero invalido non blocca gli altri
"""

import json
import os
from pathlib import Path
import asyncpg
import structlog
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
log = structlog.get_logger()

# Raggio massimo entro cui associare un POI a un sentiero (metri)
MAX_ASSOCIATION_DISTANCE_M = 500


async def get_connection() -> asyncpg.Connection:
    """Apre una connessione usando l'utente ETL (write)."""
    dsn = os.environ["ETL_DATABASE_URL"]
    conn = await asyncpg.connect(dsn)
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads,
                              schema="pg_catalog")
    return conn


# ---------------------------------------------------------------------------
# UPSERT trail — transazione per-record
# ---------------------------------------------------------------------------
async def upsert_trails(conn: asyncpg.Connection, trails: list[dict]) -> list[int]:
    """
    Inserisce o aggiorna i sentieri uno alla volta in transazioni separate.
    Un record invalido viene loggato e saltato senza bloccare gli altri.
    Restituisce la lista di trail_id inseriti/aggiornati.
    """
    trail_ids: list[int] = []
    errors = 0

    for t in trails:
        geom_geojson = json.dumps(t["geometry"])
        trailhead_geojson = json.dumps({
            "type": "Point",
            "coordinates": [t["trailhead"]["lon"], t["trailhead"]["lat"]]
        })
        try:
            async with conn.transaction():
                row = await conn.fetchrow("""
                    INSERT INTO trails (
                        osm_id, name, ref, difficulty, surface,
                        distance_m, elevation_gain_m, elevation_loss_m,
                        elevation_min_m, elevation_max_m,
                        geometry, trailhead, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5,
                        $6, $7, $8,
                        $9, $10,
                        ST_SetSRID(ST_GeomFromGeoJSON($11), 4326),
                        ST_SetSRID(ST_GeomFromGeoJSON($12), 4326),
                        NOW()
                    )
                    ON CONFLICT (osm_id) DO UPDATE SET
                        name             = EXCLUDED.name,
                        ref              = EXCLUDED.ref,
                        difficulty       = EXCLUDED.difficulty,
                        surface          = EXCLUDED.surface,
                        distance_m       = EXCLUDED.distance_m,
                        elevation_gain_m = EXCLUDED.elevation_gain_m,
                        elevation_loss_m = EXCLUDED.elevation_loss_m,
                        elevation_min_m  = EXCLUDED.elevation_min_m,
                        elevation_max_m  = EXCLUDED.elevation_max_m,
                        geometry         = EXCLUDED.geometry,
                        trailhead        = EXCLUDED.trailhead,
                        updated_at       = NOW()
                    RETURNING id
                """,
                    t["osm_id"], t.get("name"), t.get("ref"),
                    t.get("difficulty"), t.get("surface"),
                    t.get("distance_m"), t.get("elevation_gain_m"),
                    t.get("elevation_loss_m"), t.get("elevation_min_m"),
                    t.get("elevation_max_m"), geom_geojson, trailhead_geojson
                )
            trail_ids.append(row["id"])
        except Exception as e:
            errors += 1
            log.error("load.trail_error", osm_id=t["osm_id"], error=str(e))

    log.info("load.trails", inserted=len(trail_ids), errors=errors)
    return trail_ids


# ---------------------------------------------------------------------------
# UPSERT POI — transazione per-record
# ---------------------------------------------------------------------------
async def upsert_shelters(conn: asyncpg.Connection, shelters: list[dict]) -> None:
    errors = 0
    for s in shelters:
        geojson = json.dumps({
            "type": "Point",
            "coordinates": [s["location"]["lon"], s["location"]["lat"]]
        })
        try:
            async with conn.transaction():
                await conn.execute("""
                    INSERT INTO shelters
                        (osm_id, name, elevation_m, opening_hours, capacity, location)
                    VALUES ($1, $2, $3, $4, $5, ST_SetSRID(ST_GeomFromGeoJSON($6), 4326))
                    ON CONFLICT (osm_id) DO UPDATE SET
                        name          = EXCLUDED.name,
                        elevation_m   = EXCLUDED.elevation_m,
                        opening_hours = EXCLUDED.opening_hours,
                        capacity      = EXCLUDED.capacity,
                        location      = EXCLUDED.location
                """, s["osm_id"], s["name"], s.get("elevation_m"),
                    s.get("opening_hours"), s.get("capacity"), geojson)
        except Exception as e:
            errors += 1
            log.error("load.shelter_error", osm_id=s["osm_id"], error=str(e))
    log.info("load.shelters", inserted=len(shelters) - errors, errors=errors)


async def upsert_water_sources(conn: asyncpg.Connection, sources: list[dict]) -> None:
    errors = 0
    for w in sources:
        geojson = json.dumps({
            "type": "Point",
            "coordinates": [w["location"]["lon"], w["location"]["lat"]]
        })
        try:
            async with conn.transaction():
                await conn.execute("""
                    INSERT INTO water_sources (osm_id, name, location)
                    VALUES ($1, $2, ST_SetSRID(ST_GeomFromGeoJSON($3), 4326))
                    ON CONFLICT (osm_id) DO UPDATE SET
                        name     = EXCLUDED.name,
                        location = EXCLUDED.location
                """, w["osm_id"], w.get("name"), geojson)
        except Exception as e:
            errors += 1
            log.error("load.water_error", osm_id=w["osm_id"], error=str(e))
    log.info("load.water_sources", inserted=len(sources) - errors, errors=errors)


async def upsert_parkings(conn: asyncpg.Connection, parkings: list[dict]) -> None:
    errors = 0
    for p in parkings:
        geojson = json.dumps({
            "type": "Point",
            "coordinates": [p["location"]["lon"], p["location"]["lat"]]
        })
        try:
            async with conn.transaction():
                await conn.execute("""
                    INSERT INTO parkings (osm_id, name, location)
                    VALUES ($1, $2, ST_SetSRID(ST_GeomFromGeoJSON($3), 4326))
                    ON CONFLICT (osm_id) DO UPDATE SET
                        name     = EXCLUDED.name,
                        location = EXCLUDED.location
                """, p["osm_id"], p.get("name"), geojson)
        except Exception as e:
            errors += 1
            log.error("load.parking_error", osm_id=p["osm_id"], error=str(e))
    log.info("load.parkings", inserted=len(parkings) - errors, errors=errors)


# ---------------------------------------------------------------------------
# Associazioni trail <-> POI (via PostGIS ST_Distance)
# ---------------------------------------------------------------------------
async def associate_pois(conn: asyncpg.Connection) -> None:
    """
    Popola le join table trail_shelters, trail_water_sources, trail_parkings.
    Associa ogni POI ai sentieri che passano entro MAX_ASSOCIATION_DISTANCE_M.
    Usa ST_Distance su geometrie geografiche (gradi -> metri con ::geography).
    """
    async with conn.transaction():
        await conn.execute(
            "TRUNCATE trail_shelters, trail_water_sources, trail_parkings"
        )

        await conn.execute("""
            INSERT INTO trail_shelters (trail_id, shelter_id, distance_m)
            SELECT t.id, s.id,
                   ROUND(ST_Distance(t.geometry::geography, s.location::geography))::int
            FROM trails t, shelters s
            WHERE ST_DWithin(t.geometry::geography, s.location::geography, $1)
            ON CONFLICT DO NOTHING
        """, float(MAX_ASSOCIATION_DISTANCE_M))

        await conn.execute("""
            INSERT INTO trail_water_sources (trail_id, water_source_id, distance_m)
            SELECT t.id, w.id,
                   ROUND(ST_Distance(t.geometry::geography, w.location::geography))::int
            FROM trails t, water_sources w
            WHERE ST_DWithin(t.geometry::geography, w.location::geography, $1)
            ON CONFLICT DO NOTHING
        """, float(MAX_ASSOCIATION_DISTANCE_M))

        await conn.execute("""
            INSERT INTO trail_parkings (trail_id, parking_id, distance_m)
            SELECT t.id, p.id,
                   ROUND(ST_Distance(t.geometry::geography, p.location::geography))::int
            FROM trails t, parkings p
            WHERE ST_DWithin(t.geometry::geography, p.location::geography, $1)
            ON CONFLICT DO NOTHING
        """, float(MAX_ASSOCIATION_DISTANCE_M))

    counts = await conn.fetchrow("""
        SELECT
            (SELECT COUNT(*) FROM trail_shelters)      AS shelters,
            (SELECT COUNT(*) FROM trail_water_sources) AS water,
            (SELECT COUNT(*) FROM trail_parkings)      AS parkings
    """)
    log.info("load.associations", **dict(counts))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
async def load_all(data: dict) -> None:
    """
    Carica tutti i dati estratti nel DB.
    data deve contenere: trails, shelters, water_sources, parkings.
    """
    conn = await get_connection()
    try:
        await upsert_trails(conn, data["trails"])
        await upsert_shelters(conn, data["shelters"])
        await upsert_water_sources(conn, data["water_sources"])
        await upsert_parkings(conn, data["parkings"])
        await associate_pois(conn)
        log.info("load.complete")
    finally:
        await conn.close()
