"""
Modelli dati — hikesmap API

Convenzioni:
- Campi con source="osm"      → popolati automaticamente dall'ETL via OpenStreetMap
- Campi con source="osm/unreliable" → presenti in OSM ma copertura lacunosa; potrebbero essere null
- Campi con source="manual"   → richiedono fonti esterne o contributi degli utenti (vedi NOTE)
- Campi con source="derived"  → calcolati dall'ETL (es. da DEM Copernicus)
"""

from pydantic import BaseModel, Field
from typing import Optional


# ---------------------------------------------------------------------------
# Sotto-modelli
# ---------------------------------------------------------------------------

class Point(BaseModel):
    """Coordinata geografica (longitudine, latitudine)."""
    lon: float
    lat: float


class WaterSource(BaseModel):
    """Fonte d'acqua lungo il percorso."""
    name: Optional[str] = None          # source: osm/unreliable
    location: Point                     # source: osm/unreliable
    osm_id: Optional[int] = None        # source: osm/unreliable


class Shelter(BaseModel):
    """Rifugio alpino incrociato lungo il percorso."""
    name: str                           # source: osm
    location: Point                     # source: osm
    osm_id: int                         # source: osm
    elevation_m: Optional[int] = None   # source: osm (tag ele=*)
    opening_hours: Optional[str] = None # source: osm (tag opening_hours=*)
    capacity: Optional[int] = None      # source: osm (tag capacity=*)


class Parking(BaseModel):
    """Informazioni sul parcheggio al trailhead."""
    available: Optional[bool] = None
    # NOTE: OSM mappa i parcheggi come entità separate, non associate al sentiero.
    # L'ETL tenta di rilevare parcheggi entro 200m dal trailhead, ma il dato
    # è inaffidabile. Campo da validare manualmente o tramite contributi utenti.
    # Fonti alternative da valutare: OpenAlpMaps, dati CAI, schede rifugi CAI.
    notes: Optional[str] = None         # source: manual — es. "50 posti, chiuso dicembre-aprile"
    osm_id: Optional[int] = None        # source: osm/unreliable


# ---------------------------------------------------------------------------
# Modello principale: sentiero
# ---------------------------------------------------------------------------

class Trail(BaseModel):
    """Rappresentazione completa di un sentiero escursionistico."""

    # --- Identificazione ---
    id: int                             # source: derived (generato dal DB)
    osm_id: int                         # source: osm
    name: Optional[str] = None          # source: osm (tag name=*)
    ref: Optional[str] = None           # source: osm (tag ref=*, es. "GTA", "101")

    # --- Caratteristiche ---
    difficulty: Optional[str] = None    # source: osm (tag sac_scale=* mappato su T1-T6 CAI)
    surface: Optional[str] = None       # source: osm (tag surface=*)
    distance_m: Optional[int] = None    # source: derived (calcolato dalla geometria)
    elevation_gain_m: Optional[int] = None   # source: derived (da DEM Copernicus 30m)
    elevation_loss_m: Optional[int] = None   # source: derived
    elevation_min_m: Optional[int] = None    # source: derived
    elevation_max_m: Optional[int] = None    # source: derived

    # --- Geografico ---
    geometry: dict = Field(...)         # source: osm — GeoJSON LineString
    bbox: list[float] = Field(...)      # source: derived — [minLon, minLat, maxLon, maxLat]
    region: Optional[str] = None        # source: derived (reverse geocoding sul trailhead)

    # --- Punto di partenza ---
    trailhead: Optional[Point] = None   # source: derived (primo punto della geometria)
    trailhead_name: Optional[str] = None # source: osm/unreliable (nodo OSM più vicino con name=*)

    # --- Parcheggio ---
    parking: Optional[Parking] = None
    # NOTE: vedere commento in Parking. Dato inaffidabile da OSM.
    # Da valutare integrazione con: CAI (schede sentieri), OpenAlpMaps, contributi utenti.

    # --- Fonti d'acqua ---
    water_at_start: Optional[bool] = None
    # NOTE: OSM ha il tag amenity=drinking_water ma la copertura in area montana
    # è molto lacunosa. Il dato null va inteso come "sconosciuto", non come assenza.
    # Fonti alternative da valutare: schede CAI, siti dei parchi regionali.
    water_sources: list[WaterSource] = Field(default_factory=list)
    # source: osm/unreliable — estratti entro 100m dalla geometria del sentiero

    # --- Rifugi ---
    shelters: list[Shelter] = Field(default_factory=list)
    # source: osm — tourism=alpine_hut entro 150m dalla geometria. Copertura buona
    # sulle Alpi italiane. Dati verificabili su rifugi.cai.it.

    # --- Metadati ---
    updated_at: Optional[str] = None    # source: osm (tag timestamp del way OSM)


class TrailList(BaseModel):
    """Risposta paginata dell'endpoint /trails."""
    trails: list[Trail]
    total: int
    limit: int
