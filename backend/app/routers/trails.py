from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from asyncpg import Connection
from typing import Any, Dict, List, Optional
import json

from app.database import get_db
from app.models import (
    TrailFeature, TrailProperties, LineStringGeometry,
    ElevationProfile, ElevationSample,
)

router = APIRouter(prefix="/trails", tags=["trails"])


@router.get("/{trail_id}", response_model=TrailFeature)
async def get_trail(
    trail_id: int,
    db: Connection = Depends(get_db),
) -> TrailFeature:
    """Ritorna il sentiero come GeoJSON Feature con geometria completa."""
    row = await db.fetchrow(
        """
        SELECT id, name, cai_ref, difficulty, network,
               length_km, elevation_gain_m, elevation_loss_m,
               duration_hours, tags, osm_url,
               ST_AsGeoJSON(geom)::json AS geometry
        FROM trails
        WHERE id = $1
        """,
        trail_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Sentiero non trovato")

    geom_data = row["geometry"]
    if isinstance(geom_data, str):
        geom_data = json.loads(geom_data)

    geometry = LineStringGeometry(coordinates=geom_data["coordinates"])

    return TrailFeature(
        geometry=geometry,
        properties=TrailProperties(
            id=row["id"],
            name=row["name"],
            cai_ref=row["cai_ref"],
            difficulty=row["difficulty"],
            length_km=row["length_km"],
            elevation_gain_m=row["elevation_gain_m"],
            elevation_loss_m=row["elevation_loss_m"],
            duration_hours=row["duration_hours"],
            tags=list(row["tags"]) if row["tags"] else None,
            osm_url=row["osm_url"],
        ),
    )


@router.get("/{trail_id}/elevation", response_model=ElevationProfile)
async def get_elevation(
    trail_id: int,
    db: Connection = Depends(get_db),
) -> ElevationProfile:
    """Ritorna il profilo altimetrico del sentiero."""
    row = await db.fetchrow(
        """
        SELECT elevation_profile, elevation_gain_m, elevation_loss_m
        FROM trails
        WHERE id = $1
        """,
        trail_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Sentiero non trovato")
    if row["elevation_profile"] is None:
        raise HTTPException(status_code=404, detail="Profilo altimetrico non disponibile")

    raw_profile = row["elevation_profile"]
    # elevation_profile è JSONB: lista di {d_km, alt_m}
    if isinstance(raw_profile, str):
        raw_profile = json.loads(raw_profile)

    profile = [ElevationSample(d_km=p["d_km"], alt_m=p["alt_m"]) for p in raw_profile]
    altitudes = [p.alt_m for p in profile]

    return ElevationProfile(
        profile=profile,
        gain_m=row["elevation_gain_m"] or 0,
        loss_m=row["elevation_loss_m"] or 0,
        max_alt_m=int(max(altitudes)) if altitudes else 0,
        min_alt_m=int(min(altitudes)) if altitudes else 0,
    )


@router.get("/{trail_id}/gpx")
async def get_gpx(
    trail_id: int,
    db: Connection = Depends(get_db),
) -> Response:
    """Ritorna il tracciato GPX del sentiero come file da scaricare."""
    row = await db.fetchrow(
        """
        SELECT name, cai_ref, ST_AsGeoJSON(geom)::json AS geometry
        FROM trails
        WHERE id = $1
        """,
        trail_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Sentiero non trovato")

    geom_data = row["geometry"]
    if isinstance(geom_data, str):
        geom_data = json.loads(geom_data)

    coords = geom_data.get("coordinates", [])
    trail_name = row["name"] or f"Sentiero {trail_id}"

    trkpts = "\n    ".join(
        f'<trkpt lat="{c[1]:.6f}" lon="{c[0]:.6f}">'
        + (f"<ele>{c[2]:.1f}</ele>" if len(c) > 2 else "")
        + "</trkpt>"
        for c in coords
    )

    gpx_content = f"""<?xml version='1.0' encoding='UTF-8'?>
<gpx version='1.1' creator='Trail Explorer'
     xmlns='http://www.topografix.com/GPX/1/1'>
  <trk>
    <name>{trail_name}</name>
    <trkseg>
    {trkpts}
    </trkseg>
  </trk>
</gpx>"""

    return Response(
        content=gpx_content,
        media_type="application/gpx+xml",
        headers={
            "Content-Disposition": f'attachment; filename="sentiero_{trail_id}.gpx"'
        },
    )


@router.get("/{trail_id}/geometry")
async def get_geometry(
    trail_id: int,
    db: Connection = Depends(get_db),
) -> Dict[str, Any]:
    """Ritorna la geometria semplificata del sentiero come GeoJSON FeatureCollection."""
    row = await db.fetchrow(
        """
        SELECT id, difficulty,
               COALESCE(
                   ST_AsGeoJSON(geom_simplified_z12)::json,
                   ST_AsGeoJSON(geom)::json
               ) AS geometry,
               ST_Extent(COALESCE(geom_simplified_z12, geom)) OVER () AS bbox_raw
        FROM trails
        WHERE id = $1
        """,
        trail_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Sentiero non trovato")

    geom_data = row["geometry"]
    if isinstance(geom_data, str):
        geom_data = json.loads(geom_data)

    # Calcola bbox dalla geometria stessa (ST_Extent in window non funziona su 1 riga)
    bbox_row = await db.fetchrow(
        """
        SELECT ST_XMin(ext) AS xmin, ST_YMin(ext) AS ymin,
               ST_XMax(ext) AS xmax, ST_YMax(ext) AS ymax
        FROM (
            SELECT ST_Extent(COALESCE(geom_simplified_z12, geom)) AS ext
            FROM trails WHERE id = $1
        ) sub
        """,
        trail_id,
    )

    bbox = None
    if bbox_row and bbox_row["xmin"] is not None:
        bbox = [
            float(bbox_row["xmin"]),
            float(bbox_row["ymin"]),
            float(bbox_row["xmax"]),
            float(bbox_row["ymax"]),
        ]

    feature = {
        "type": "Feature",
        "geometry": geom_data,
        "properties": {
            "id": row["id"],
            "difficulty": row["difficulty"],
        },
    }

    result: Dict[str, Any] = {
        "type": "FeatureCollection",
        "features": [feature],
    }
    if bbox:
        result["bbox"] = bbox

    return result
