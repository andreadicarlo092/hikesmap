"""
etl/extract.py — Estrae sentieri e POI dai file OSM e calcola i dati altimetrici.

Flusso:
  1. Legge il file .osm.pbf con osmium
  2. Estrae i way con tag highway=path/footway/track + sac_scale=* (sentieri CAI)
  3. Estrae rifugi (tourism=alpine_hut), fonti d'acqua (amenity=drinking_water),
     parcheggi (amenity=parking) entro il bbox del Nord Italia
  4. Campiona il DEM Copernicus lungo ogni sentiero per calcolare
     dislivello, quota min/max
  5. Restituisce dizionari pronti per il caricamento in PostGIS

Sicurezza:
  - Tutti i valori da OSM vengono trattati come input non fidati
  - I campi stringa vengono troncati a lunghezza massima
  - Le geometrie vengono validate prima del caricamento
"""

import math
from pathlib import Path
from typing import Any
import osmium
import structlog
from shapely.geometry import LineString, mapping
import pyproj

log = structlog.get_logger()

# Scala SAC (OSM) -> difficoltà CAI
SAC_TO_CAI = {
    "hiking":                    "T1",
    "mountain_hiking":           "T2",
    "demanding_mountain_hiking": "T3",
    "alpine_hiking":             "T4",
    "demanding_alpine_hiking":   "T5",
    "difficult_alpine_hiking":   "T6",
}

# Limiti di sanitizzazione per i campi stringa OSM (input non fidato)
MAX_NAME_LEN    = 255
MAX_REF_LEN     = 50
MAX_SURFACE_LEN = 100

# BBox Nord Italia (filtro geografico grezzo)
NORD_ITALIA_BBOX = (6.0, 43.5, 14.5, 47.8)  # (min_lon, min_lat, max_lon, max_lat)


def _sanitize_str(value: str | None, max_len: int) -> str | None:
    """Tronca e pulisce una stringa proveniente da OSM."""
    if not value:
        return None
    v = value.strip()
    return v[:max_len] if v else None


def _parse_elevation(raw: str | None) -> int | None:
    """
    Converte un valore di quota OSM in intero.
    Gestisce: "1234", "1234.5", "1234 m", "1234m".
    Restituisce None se il valore non è parsabile.
    """
    if not raw:
        return None
    try:
        return round(float(raw.strip().rstrip("m").strip()))
    except (ValueError, AttributeError):
        return None


def _in_bbox(lon: float, lat: float, bbox: tuple) -> bool:
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat


# ---------------------------------------------------------------------------
# Handler osmium per i sentieri
# ---------------------------------------------------------------------------
class TrailHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.trails: list[dict] = []

    def way(self, w):
        tags = w.tags
        # Filtra solo sentieri con sac_scale (sentieri alpini classificati)
        if tags.get("highway") not in ("path", "footway", "track"):
            return
        if "sac_scale" not in tags:
            return

        # Costruisce la geometria dai nodi (locations=True richiesto in apply_file)
        coords = [(n.lon, n.lat) for n in w.nodes if n.location.valid()]
        if len(coords) < 2:
            return

        try:
            line = LineString(coords)
        except Exception:
            return

        if not line.is_valid:
            return

        # Filtro geografico sul centroide
        centroid = line.centroid
        if not _in_bbox(centroid.x, centroid.y, NORD_ITALIA_BBOX):
            return

        self.trails.append({
            "osm_id":    w.id,
            "name":      _sanitize_str(tags.get("name"),    MAX_NAME_LEN),
            "ref":       _sanitize_str(tags.get("ref"),     MAX_REF_LEN),
            "difficulty": SAC_TO_CAI.get(tags.get("sac_scale", ""), None),
            "surface":   _sanitize_str(tags.get("surface"), MAX_SURFACE_LEN),
            "geometry":  mapping(line),                           # GeoJSON LineString
            "coords":    list(line.coords),                       # usato per campionamento DEM
            "trailhead": {"lon": coords[0][0], "lat": coords[0][1]},
            "bbox":      list(line.bounds),
        })


# ---------------------------------------------------------------------------
# Handler osmium per i POI
# ---------------------------------------------------------------------------
class POIHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.shelters:      list[dict] = []
        self.water_sources: list[dict] = []
        self.parkings:      list[dict] = []

    def node(self, n):
        if not n.location.valid():
            return
        lon, lat = n.location.lon, n.location.lat
        if not _in_bbox(lon, lat, NORD_ITALIA_BBOX):
            return

        tags = n.tags
        tourism = tags.get("tourism", "")
        amenity = tags.get("amenity", "")

        if tourism == "alpine_hut":
            self.shelters.append({
                "osm_id":        n.id,
                "name":          _sanitize_str(tags.get("name"), MAX_NAME_LEN) or "Rifugio senza nome",
                "elevation_m":   _parse_elevation(tags.get("ele")),
                "opening_hours": _sanitize_str(tags.get("opening_hours"), 255),
                "capacity":      _parse_elevation(tags.get("capacity")),  # stesso parsing int
                "location":      {"lon": lon, "lat": lat},
            })

        elif amenity == "drinking_water":
            self.water_sources.append({
                "osm_id":   n.id,
                "name":     _sanitize_str(tags.get("name"), MAX_NAME_LEN),
                "location": {"lon": lon, "lat": lat},
            })

        elif amenity == "parking":
            self.parkings.append({
                "osm_id":   n.id,
                "name":     _sanitize_str(tags.get("name"), MAX_NAME_LEN),
                "location": {"lon": lon, "lat": lat},
            })


# ---------------------------------------------------------------------------
# Calcolo altimetrico da DEM
# ---------------------------------------------------------------------------
def sample_elevation(coords: list[tuple], dem_paths: list[Path]) -> dict[str, Any]:
    """
    Campiona il DEM Copernicus lungo le coordinate del sentiero.
    Restituisce: distance_m, elevation_gain_m, elevation_loss_m, min, max.
    Se nessun tile DEM copre il sentiero, i campi altimetrici sono None.
    """
    try:
        import rasterio
    except ImportError:
        log.warning("dem.rasterio_not_available")
        return {
            "distance_m": _calc_distance(coords),
            "elevation_gain_m": None, "elevation_loss_m": None,
            "elevation_min_m": None,  "elevation_max_m": None,
        }

    elevations = [
        e for e in (_sample_single_point(lon, lat, dem_paths) for lon, lat in coords)
        if e is not None
    ]

    distance_m = _calc_distance(coords)

    if not elevations:
        return {
            "distance_m": distance_m,
            "elevation_gain_m": None, "elevation_loss_m": None,
            "elevation_min_m": None,  "elevation_max_m": None,
        }

    gain = sum(max(0.0, elevations[i] - elevations[i - 1]) for i in range(1, len(elevations)))
    loss = sum(max(0.0, elevations[i - 1] - elevations[i]) for i in range(1, len(elevations)))

    return {
        "distance_m":       distance_m,
        "elevation_gain_m": round(gain),
        "elevation_loss_m": round(loss),
        "elevation_min_m":  round(min(elevations)),
        "elevation_max_m":  round(max(elevations)),
    }


def _sample_single_point(lon: float, lat: float, dem_paths: list[Path]) -> float | None:
    """Legge la quota di un singolo punto dai tile DEM disponibili."""
    import rasterio
    for path in dem_paths:
        try:
            with rasterio.open(path) as src:
                b = src.bounds
                if b.left <= lon <= b.right and b.bottom <= lat <= b.top:
                    row, col = src.index(lon, lat)
                    data = src.read(1, window=((row, row + 1), (col, col + 1)))
                    val = float(data[0][0])
                    if val != src.nodata and not math.isnan(val):
                        return val
        except Exception:
            continue
    return None


def _calc_distance(coords: list[tuple]) -> int:
    """Calcola la lunghezza del tracciato in metri (ellissoide WGS84)."""
    if len(coords) < 2:
        return 0
    geod = pyproj.Geod(ellps="WGS84")
    total = 0.0
    for i in range(1, len(coords)):
        _, _, dist = geod.inv(coords[i - 1][0], coords[i - 1][1],
                              coords[i][0],     coords[i][1])
        total += dist
    return round(total)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def extract_all(osm_paths: list[Path], dem_paths: list[Path]) -> dict:
    """
    Processa tutti i file OSM e restituisce trails, shelters, water_sources, parkings.
    """
    all_trails:   list[dict] = []
    all_shelters: list[dict] = []
    all_water:    list[dict] = []
    all_parkings: list[dict] = []

    for osm_path in osm_paths:
        log.info("extract.start", file=str(osm_path))

        trail_handler = TrailHandler()
        trail_handler.apply_file(str(osm_path), locations=True)
        log.info("extract.trails", count=len(trail_handler.trails), file=str(osm_path))

        poi_handler = POIHandler()
        poi_handler.apply_file(str(osm_path))
        log.info("extract.pois",
                 shelters=len(poi_handler.shelters),
                 water=len(poi_handler.water_sources),
                 parkings=len(poi_handler.parkings))

        # Calcolo altimetrico per ogni sentiero
        for trail in trail_handler.trails:
            elev = sample_elevation(trail.pop("coords"), dem_paths)
            trail.update(elev)

        all_trails.extend(trail_handler.trails)
        all_shelters.extend(poi_handler.shelters)
        all_water.extend(poi_handler.water_sources)
        all_parkings.extend(poi_handler.parkings)

    # Deduplicazione per osm_id (un sentiero può apparire in più file regionali)
    return {
        "trails":        list({t["osm_id"]: t for t in all_trails}.values()),
        "shelters":      list({s["osm_id"]: s for s in all_shelters}.values()),
        "water_sources": list({w["osm_id"]: w for w in all_water}.values()),
        "parkings":      list({p["osm_id"]: p for p in all_parkings}.values()),
    }
