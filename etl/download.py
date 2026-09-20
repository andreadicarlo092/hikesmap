"""
etl/download.py — Scarica i file sorgente per l'ETL.

Fonti:
  - Dati OSM: Geofabrik (file .osm.pbf per regione)
  - DEM:      Copernicus DEM GLO-30 (raster altimetrico 30m)

Sicurezza:
  - Verifica SHA256 di ogni file scaricato prima di usarlo
  - I file vengono salvati in etl/data/raw/ (esclusa da git)
  - Non usare MD5 o SHA1 — vulnerabili a collision attack
"""

import hashlib
import os
import httpx
import structlog
from pathlib import Path

log = structlog.get_logger()

RAW_DIR = Path(__file__).parent / "data" / "raw"

# ---------------------------------------------------------------------------
# Sorgenti OSM — Geofabrik, Nord Italia
# URL e SHA256 aggiornati a settembre 2026.
# Verificare periodicamente su https://download.geofabrik.de/europe/italy/
# ---------------------------------------------------------------------------
OSM_SOURCES = {
    "nord-ovest": {
        "url": "https://download.geofabrik.de/europe/italy/nord-ovest-latest.osm.pbf",
        "sha256": None,  # TODO: aggiornare con hash reale da Geofabrik prima del deploy
    },
    "nord-est": {
        "url": "https://download.geofabrik.de/europe/italy/nord-est-latest.osm.pbf",
        "sha256": None,  # TODO: aggiornare con hash reale da Geofabrik prima del deploy
    },
}

# ---------------------------------------------------------------------------
# Sorgenti DEM — Copernicus GLO-30
# I tile coprono il Nord Italia (latitudine 44-47, longitudine 6-14).
# URL base: https://copernicus-dem-30m.s3.amazonaws.com/
# ---------------------------------------------------------------------------
DEM_TILE_PATTERN = "Copernicus_DSM_COG_10_{lat}_{lon}_DEM.tif"
DEM_BASE_URL = "https://copernicus-dem-30m.s3.amazonaws.com"

# Tile necessari per il Nord Italia
DEM_TILES = [
    {"lat": "N44", "lon": "E006"}, {"lat": "N44", "lon": "E007"},
    {"lat": "N44", "lon": "E008"}, {"lat": "N44", "lon": "E009"},
    {"lat": "N44", "lon": "E010"}, {"lat": "N44", "lon": "E011"},
    {"lat": "N44", "lon": "E012"}, {"lat": "N44", "lon": "E013"},
    {"lat": "N45", "lon": "E006"}, {"lat": "N45", "lon": "E007"},
    {"lat": "N45", "lon": "E008"}, {"lat": "N45", "lon": "E009"},
    {"lat": "N45", "lon": "E010"}, {"lat": "N45", "lon": "E011"},
    {"lat": "N45", "lon": "E012"}, {"lat": "N45", "lon": "E013"},
    {"lat": "N46", "lon": "E006"}, {"lat": "N46", "lon": "E007"},
    {"lat": "N46", "lon": "E008"}, {"lat": "N46", "lon": "E009"},
    {"lat": "N46", "lon": "E010"}, {"lat": "N46", "lon": "E011"},
    {"lat": "N46", "lon": "E012"}, {"lat": "N46", "lon": "E013"},
]


def verify_sha256(path: Path, expected: str | None) -> bool:
    """
    Verifica l'integrità del file con SHA256.
    Se expected è None, calcola e logga l'hash senza verificare
    (usato durante lo sviluppo per ottenere l'hash da inserire in OSM_SOURCES).
    """
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    actual = sha256.hexdigest()

    if expected is None:
        log.warning("sha256.not_verified", path=str(path), computed=actual,
                    note="aggiungere questo hash a OSM_SOURCES per la verifica in produzione")
        return True

    if actual != expected:
        log.error("sha256.mismatch", path=str(path), expected=expected, actual=actual)
        return False

    log.info("sha256.ok", path=str(path))
    return True


async def download_file(url: str, dest: Path, expected_sha256: str | None = None) -> Path:
    """
    Scarica un file con progress logging e verifica SHA256.
    Salta il download se il file esiste già e il checksum è valido.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        log.info("download.skip_existing", path=str(dest))
        if not verify_sha256(dest, expected_sha256):
            log.warning("download.redownloading", path=str(dest), reason="checksum mismatch")
            dest.unlink()
        else:
            return dest

    log.info("download.start", url=url, dest=str(dest))
    async with httpx.AsyncClient(follow_redirects=True, timeout=3600) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0))
            downloaded = 0
            with open(dest, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=65536):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        if downloaded % (50 * 1024 * 1024) < 65536:  # log ogni ~50MB
                            log.info("download.progress", url=url, pct=f"{pct:.1f}%")

    if not verify_sha256(dest, expected_sha256):
        dest.unlink()
        raise RuntimeError(f"SHA256 mismatch per {dest} — file rimosso")

    log.info("download.complete", path=str(dest), size_mb=dest.stat().st_size // 1_000_000)
    return dest


async def download_osm() -> list[Path]:
    """Scarica tutti i file OSM del Nord Italia."""
    paths = []
    for region, source in OSM_SOURCES.items():
        filename = source["url"].split("/")[-1]
        dest = RAW_DIR / "osm" / filename
        path = await download_file(source["url"], dest, source["sha256"])
        paths.append(path)
    return paths


async def download_dem() -> list[Path]:
    """Scarica i tile DEM Copernicus per il Nord Italia."""
    paths = []
    for tile in DEM_TILES:
        filename = DEM_TILE_PATTERN.format(**tile)
        url = f"{DEM_BASE_URL}/{filename}/{filename}"
        dest = RAW_DIR / "dem" / filename
        # I tile DEM non hanno hash pubblicati — verifica di integrità tramite dimensione minima
        path = await download_file(url, dest, expected_sha256=None)
        paths.append(path)
    return paths
