"""
Step 4: Calcola le geometrie semplificate (LOD) per zoom 8 e 12.
ST_SimplifyPreserveTopology con tolleranze diverse.
"""
import logging
from db import get_connection

logger = logging.getLogger(__name__)


def compute_lod():
    """Genera geom_simplified_z8 e geom_simplified_z12 per tutti i trail."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # LOD zoom 8-10: tolleranza 0.01 (~1 km)
            cur.execute("""
                UPDATE trails
                SET geom_simplified_z8 = ST_SimplifyPreserveTopology(geom, 0.01)
                WHERE geom IS NOT NULL
                  AND (geom_simplified_z8 IS NULL OR updated_at > imported_at);
            """)
            n_z8 = cur.rowcount

            # LOD zoom 12-13: tolleranza 0.001 (~100 m)
            cur.execute("""
                UPDATE trails
                SET geom_simplified_z12 = ST_SimplifyPreserveTopology(geom, 0.001)
                WHERE geom IS NOT NULL
                  AND (geom_simplified_z12 IS NULL OR updated_at > imported_at);
            """)
            n_z12 = cur.rowcount

            conn.commit()

    finally:
        conn.close()

    logger.info(f'LOD calcolato: {n_z8} trail z8, {n_z12} trail z12')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    compute_lod()
