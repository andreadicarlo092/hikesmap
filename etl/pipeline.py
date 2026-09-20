"""
etl/pipeline.py — Orchestratore dell'ETL completo.

Esecuzione:
    python -m etl.pipeline

Fasi:
  1. Download OSM (Geofabrik) + DEM (Copernicus)
  2. Estrazione sentieri e POI
  3. Caricamento in PostGIS

Flag:
  --skip-download   Usa i file già presenti in etl/data/raw/
  --dry-run         Estrae ma non carica nel DB (utile per test)
"""

import argparse
import asyncio
import time
from pathlib import Path
import structlog
import structlog.dev

# Configura logging strutturato su stdout
structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer()
    ]
)
log = structlog.get_logger()


async def run(skip_download: bool = False, dry_run: bool = False) -> None:
    from etl.download import download_osm, download_dem
    from etl.extract import extract_all
    from etl.load import load_all

    RAW_DIR = Path(__file__).parent / "data" / "raw"

    t0 = time.time()
    log.info("pipeline.start")

    # --- 1. Download --------------------------------------------------------
    if skip_download:
        log.info("pipeline.download.skipped")
        osm_paths = list((RAW_DIR / "osm").glob("*.osm.pbf"))
        dem_paths = list((RAW_DIR / "dem").glob("*.tif"))
        if not osm_paths:
            log.error("pipeline.no_osm_files", dir=str(RAW_DIR / "osm"))
            raise FileNotFoundError("Nessun file OSM trovato. Rimuovi --skip-download.")
        log.info("pipeline.download.existing", osm=len(osm_paths), dem=len(dem_paths))
    else:
        log.info("pipeline.download.start")
        osm_paths = await download_osm()
        dem_paths = await download_dem()
        log.info("pipeline.download.done",
                 osm=len(osm_paths), dem=len(dem_paths),
                 elapsed_s=round(time.time() - t0))

    # --- 2. Estrazione -------------------------------------------------------
    t1 = time.time()
    log.info("pipeline.extract.start")
    data = extract_all(osm_paths, dem_paths)
    log.info("pipeline.extract.done",
             trails=len(data["trails"]),
             shelters=len(data["shelters"]),
             water_sources=len(data["water_sources"]),
             parkings=len(data["parkings"]),
             elapsed_s=round(time.time() - t1))

    # --- 3. Caricamento -------------------------------------------------------
    if dry_run:
        log.info("pipeline.load.skipped", reason="dry-run")
    else:
        t2 = time.time()
        log.info("pipeline.load.start")
        await load_all(data)
        log.info("pipeline.load.done", elapsed_s=round(time.time() - t2))

    log.info("pipeline.complete", total_elapsed_s=round(time.time() - t0))


def main():
    parser = argparse.ArgumentParser(description="hikesmap ETL pipeline")
    parser.add_argument("--skip-download", action="store_true",
                        help="Salta il download e usa i file già presenti in etl/data/raw/")
    parser.add_argument("--dry-run", action="store_true",
                        help="Estrae i dati ma non li carica nel DB")
    args = parser.parse_args()

    asyncio.run(run(skip_download=args.skip_download, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
