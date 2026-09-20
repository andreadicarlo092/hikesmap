"""
Entry point principale della pipeline ETL.
Eseguito dal container ETL: download -> filtro -> import -> trailhead -> LOD.
"""
import logging
import sys

from download import download_pbf, filter_cai_routes
from import_trails import import_trails
from trailheads import compute_trailheads
from lod import compute_lod

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('main')


def run_etl():
    logger.info('=== Trail Explorer ETL -- avvio ===')

    # Step 1: Download e filtro OSM
    logger.info('--- Step 1: Download PBF ---')
    try:
        raw_pbf = download_pbf()
        filtered_pbf = filter_cai_routes(raw_pbf)
    except Exception as e:
        logger.error(f'Step 1 fallito: {e}')
        sys.exit(1)

    # Step 2: Import trails in PostgreSQL
    logger.info('--- Step 2: Import trails ---')
    try:
        n_ok, n_err = import_trails(filtered_pbf)
        logger.info(f'Import: {n_ok} OK, {n_err} errori')
    except Exception as e:
        logger.error(f'Step 2 fallito: {e}')
        sys.exit(1)

    # Step 3: Calcolo trailhead
    logger.info('--- Step 3: Calcolo trailhead ---')
    try:
        n_th = compute_trailheads()
        logger.info(f'Trailhead draft generati: {n_th}')
    except Exception as e:
        logger.error(f'Step 3 fallito: {e}')
        sys.exit(1)

    # Step 4: LOD
    logger.info('--- Step 4: Calcolo LOD geometrie ---')
    try:
        compute_lod()
    except Exception as e:
        logger.warning(f'Step 4 (LOD) fallito (non critico): {e}')

    logger.info('=== ETL completato ===')


if __name__ == '__main__':
    run_etl()
