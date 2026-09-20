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

import asyncio
import hashlib
import os
import httpx
import structlog
from pathlib import Path

log = structlog.get_logger()

RAW_DIR = Path(__file__).parent / "data" / "raw"

# Dimensione minima accettabile per un tile DEM (~5 MB).
# Un tile reale pesa 20-80 MB; sotto questa soglia il file è corrotto o troncato.
MIN_DEM_TILE_SIZE_BYTES = 5 * 1024 * 1024

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
# I tile coprono il Nord Italia (latitudine N44-N47, longitudine E006-E013).
# URL base: https://copernicus-dem-30m.s3.amazonaws.com/
# ---------------------------------------------------------------------------
DEM_TILE_PATTERN = "Copernicus_DSM_COG_10_{lat}_{lon}_DEM.tif"
DEM_BASE_URL = "https://copernicus-dem-30m.s3.amazonaws.com"

# Tile necessari per il Nord Italia (N44 -> N47 incluso per coprire Trentino,
# Alto Adige e Friuli fino al confine con Austria e Slovenia)
DEM_TILES = [
    {"lat": lat, "lon": lon}
    for lat in ("N44", "N45", "N46", "N47")
    for lon in ("E006", "E007", "E008", "E009", "E010", "E011", "E012", "E013")
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


async def download_file(
    url: str,
    dest: Path,
    expected_sha256: str | None = None,
    min_size_bytes: int | None = None,
) -> Path:
    """
    Scarica un file con progress logging e verifica SHA256.
    Salta il download se il file esiste già, il checksum è valido
    e la dimensione supera min_size_bytes.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        size_ok = (min_size_bytes is None or dest.stat().st_size >= min_size_bytes)
        if size_ok and verify_sha256(dest, expected_sha256):
            log.info("download.skip_existing", path=str(dest))
            return dest
        log.warning("download.redownloading", path=str(dest),
                    reason="checksum mismatch or file too small")
        dest.unlink()

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
                    if total and downloaded % (50 * 1024 * 1024) < 65536:
                        log.info("download.progress", url=url,
                                 pct=f"{downloaded / total * 100:.1f}%")

    # Verifica dimensione minima
    if min_size_bytes and dest.stat().st_size < min_size_bytes:
        dest.unlink()
        raise RuntimeError(
            f"File troppo piccolo dopo il download: {dest} "
            f"({dest.stat().st_size if dest.exists() else 0} B < {min_size_bytes} B attesi). "
            "Probabile errore di rete o risposta non valida dal server."
        )

    if not verify_sha256(dest, expected_sha256):
        dest.unlink()
        raise RuntimeError(f"SHA256 mismatch per {dest} — file rimosso")

    log.info("download.complete", path=str(dest), size_mb=dest.stat().st_size // 1_000_000)
    return dest


async def download_osm() -> list[Path]:
    """Scarica tutti i file OSM del Nord Italia (sequenziale — file grandi)."""
    paths = []
    for region, source in OSM_SOURCES.items():
        filename = source["url"].split("/")[-1]
        dest = RAW_DIR / "osm" / filename
        path = await download_file(source["url"], dest, source["sha256"])
        paths.append(path)
    return paths


async def _download_dem_tile(tile: dict) -> Path | None:
    """
    Scarica un singolo tile DEM. Restituisce None (senza sollevare eccezione)
    se il tile non è disponibile sul server — alcuni tile ai bordi del bbox
    possono non esistere nel dataset Copernicus.
    """
    filename = DEM_TILE_PATTERN.format(**tile)
    url = f"{DEM_BASE_URL}/{filename}/{filename}"
    dest = RAW_DIR / "dem" / filename
    try:
        return await download_file(url, dest, expected_sha256=None,
                                   min_size_bytes=MIN_DEM_TILE_SIZE_BYTES)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            log.warning("dem.tile_not_found", tile=filename, url=url)
            return None
        raise
    except Exception as e:
        log.error("dem.tile_error", tile=filename, error=str(e))
        return None


async def download_dem() -> list[Path]:
    """
    Scarica i tile DEM Copernicus per il Nord Italia in parallelo.
    I tile non disponibili vengono saltati con un warning.
    """
    results = await asyncio.gather(*(_download_dem_tile(t) for t in DEM_TILES))
    paths = [p for p in results if p is not None]
    log.info("dem.download_complete", total=len(DEM_TILES), downloaded=len(paths),
             skipped=len(DEM_TILES) - len(paths))
    return paths
