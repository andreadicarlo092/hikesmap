import os
import subprocess
import logging

import requests as req

from config import REGIONS, DEFAULT_REGION, DATA_DIR, RAW_PBF, FILTERED_PBF

logger = logging.getLogger(__name__)


def download_pbf(region=DEFAULT_REGION):
    os.makedirs(DATA_DIR, exist_ok=True)
    url = REGIONS[region]
    logger.info(f'Download PBF: {url}')

    if os.path.exists(RAW_PBF):
        logger.info(f'PBF gia presente: {RAW_PBF} -- skip download')
        return RAW_PBF

    with req.get(url, stream=True, timeout=3600) as r:
        r.raise_for_status()
        total = int(r.headers.get('content-length', 0))
        downloaded = 0
        with open(RAW_PBF, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded / total * 100
                    if downloaded % (10 * 1024 * 1024) < 1024 * 1024:
                        logger.info(f'  {pct:.1f}% ({downloaded // 1024 // 1024} MB)')

    logger.info(f'Download completato: {RAW_PBF}')
    return RAW_PBF


def filter_cai_routes(raw_pbf=RAW_PBF, filtered_pbf=FILTERED_PBF):
    if os.path.exists(filtered_pbf):
        logger.info(f'PBF filtrato gia presente: {filtered_pbf} -- skip filtro')
        return filtered_pbf

    cmd = [
        'osmium', 'tags-filter',
        raw_pbf,
        'r/route=hiking',
        'r/cai_scale',
        '--overwrite',
        '-o', filtered_pbf,
    ]
    logger.info(f'osmium filter: {" ".join(cmd)}')
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f'osmium fallito: {result.stderr}')

    logger.info(f'Filtro completato: {filtered_pbf}')
    return filtered_pbf


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    pbf = download_pbf()
    filter_cai_routes(pbf)
