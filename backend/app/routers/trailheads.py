from fastapi import APIRouter, Depends, HTTPException, Query
from asyncpg import Connection
from typing import List

from app.database import get_db
from app.models import TrailheadCollection, TrailheadFeature, TrailheadDetail, TrailSummary, PointGeometry, TrailheadProperties

router = APIRouter(prefix="/trailheads", tags=["trailheads"])


@router.get("/", response_model=TrailheadCollection)
async def list_trailheads(
    bbox: str = Query(..., description="Bounding box formato 'w,s,e,n'"),
    limit: int = Query(500, le=2000),
    db: Connection = Depends(get_db),
) -> TrailheadCollection:
    """Ritorna i trailhead validati dentro il bounding box fornito."""
    try:
        parts = [float(x.strip()) for x in bbox.split(",")]
        if len(parts) != 4:
            raise ValueError("bbox deve avere 4 valori")
        w, s, e, n = parts
    except (ValueError, AttributeError) as exc:
        raise HTTPException(status_code=422, detail=f"bbox malformata: {exc}") from exc

    rows = await db.fetch(
        """
        SELECT id, name, trail_count,
               ST_X(geom) AS lon, ST_Y(geom) AS lat
        FROM trailheads
        WHERE validated = TRUE
          AND ST_Within(geom, ST_MakeEnvelope($1, $2, $3, $4, 4326))
        LIMIT $5
        """,
        w, s, e, n, limit,
    )

    features = [
        TrailheadFeature(
            geometry=PointGeometry(coordinates=[row["lon"], row["lat"]]),
            properties=TrailheadProperties(
                id=row["id"],
                name=row["name"],
                trail_count=row["trail_count"],
            ),
        )
        for row in rows
    ]
    return TrailheadCollection(features=features)


@router.get("/{trailhead_id}", response_model=TrailheadDetail)
async def get_trailhead(
    trailhead_id: int,
    db: Connection = Depends(get_db),
) -> TrailheadDetail:
    """Ritorna i dettagli di un singolo trailhead."""
    row = await db.fetchrow(
        """
        SELECT id, name, trail_count,
               ST_X(geom) AS lon, ST_Y(geom) AS lat
        FROM trailheads
        WHERE id = $1 AND validated = TRUE
        """,
        trailhead_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Trailhead non trovato")

    return TrailheadDetail(
        id=row["id"],
        name=row["name"],
        trail_count=row["trail_count"],
        lat=row["lat"],
        lon=row["lon"],
    )


@router.get("/{trailhead_id}/trails", response_model=List[TrailSummary])
async def list_trails_for_trailhead(
    trailhead_id: int,
    db: Connection = Depends(get_db),
) -> List[TrailSummary]:
    """Ritorna i sentieri che partono dal trailhead, ordinati per difficoltà e lunghezza."""
    # Verifica che il trailhead esista
    exists = await db.fetchval(
        "SELECT id FROM trailheads WHERE id = $1 AND validated = TRUE",
        trailhead_id,
    )
    if exists is None:
        raise HTTPException(status_code=404, detail="Trailhead non trovato")

    rows = await db.fetch(
        """
        SELECT t.id, t.name, t.cai_ref, t.difficulty,
               t.length_km, t.elevation_gain_m, t.elevation_loss_m,
               t.duration_hours, t.tags
        FROM trails t
        JOIN trail_trailhead tt ON tt.trail_id = t.id
        WHERE tt.trailhead_id = $1
        ORDER BY
            CASE t.difficulty
                WHEN 'T'   THEN 1
                WHEN 'E'   THEN 2
                WHEN 'EE'  THEN 3
                WHEN 'EEA' THEN 4
                ELSE 5
            END,
            t.length_km ASC
        """,
        trailhead_id,
    )

    return [
        TrailSummary(
            id=row["id"],
            name=row["name"],
            cai_ref=row["cai_ref"],
            difficulty=row["difficulty"],
            length_km=row["length_km"],
            elevation_gain_m=row["elevation_gain_m"],
            elevation_loss_m=row["elevation_loss_m"],
            duration_hours=row["duration_hours"],
            tags=list(row["tags"]) if row["tags"] else None,
        )
        for row in rows
    ]
