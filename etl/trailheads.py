"""
Step 3: Calcola i trailhead automatici con ST_ClusterDBSCAN
sugli endpoint (start/end) di ogni sentiero importato.
I trailhead generati sono in stato validated=FALSE (draft)
finche non approvati tramite la CLI.
"""
import logging

from db import get_connection

logger = logging.getLogger(__name__)

CLUSTER_EPS_DEG = 0.0005  # ~50m a 45 lat


def compute_trailheads() -> int:
    """
    Calcola i trailhead draft per i sentieri importati.
    Restituisce il numero di trailhead generati.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Raccoglie tutti gli endpoint (start + end) di ogni sentiero
            # ST_StartPoint e ST_EndPoint per LineString
            # Per MultiLineString usa ST_PointN sul primo e ultimo
            cur.execute("""
                CREATE TEMP TABLE IF NOT EXISTS trail_endpoints AS
                SELECT
                    id AS trail_id,
                    ST_StartPoint(
                        CASE WHEN ST_GeometryType(geom) = 'ST_LineString'
                             THEN geom
                             ELSE ST_GeometryN(geom, 1)
                        END
                    ) AS point
                FROM trails
                WHERE geom IS NOT NULL
                UNION ALL
                SELECT
                    id AS trail_id,
                    ST_EndPoint(
                        CASE WHEN ST_GeometryType(geom) = 'ST_LineString'
                             THEN geom
                             ELSE ST_GeometryN(geom, ST_NumGeometries(geom))
                        END
                    ) AS point
                FROM trails
                WHERE geom IS NOT NULL;
            """)

            # 2. Applica ST_ClusterDBSCAN
            cur.execute("""
                CREATE TEMP TABLE IF NOT EXISTS clustered_endpoints AS
                SELECT
                    trail_id,
                    point,
                    ST_ClusterDBSCAN(point, %(eps)s, 1) OVER () AS cluster_id
                FROM trail_endpoints
                WHERE point IS NOT NULL;
            """, {'eps': CLUSTER_EPS_DEG})

            # 3. Inserisce trailhead draft (skip se cluster gia esiste per quei trail)
            # Prima pulisce i draft non validati per rifarli freschi
            cur.execute("""
                DELETE FROM trail_trailhead tt
                USING trailheads th
                WHERE tt.trailhead_id = th.id AND th.validated = FALSE;
            """)
            cur.execute("""
                DELETE FROM trailheads WHERE validated = FALSE;
            """)

            # 4. Inserisce un trailhead per ogni cluster
            cur.execute("""
                INSERT INTO trailheads (geom, trail_count, source, validated)
                SELECT
                    ST_Centroid(ST_Collect(point)) AS geom,
                    COUNT(DISTINCT trail_id) AS trail_count,
                    'auto_cluster' AS source,
                    FALSE AS validated
                FROM clustered_endpoints
                WHERE cluster_id IS NOT NULL
                GROUP BY cluster_id
                RETURNING id;
            """)
            trailhead_ids = [row[0] for row in cur.fetchall()]
            n_trailheads = len(trailhead_ids)

            # 5. Costruisce la tabella trail_trailhead
            # Per ogni trail_id, trova il trailhead piu vicino tra quelli appena creati
            cur.execute("""
                INSERT INTO trail_trailhead (trail_id, trailhead_id)
                SELECT DISTINCT ON (ce.trail_id)
                    ce.trail_id,
                    th.id AS trailhead_id
                FROM clustered_endpoints ce
                JOIN trailheads th ON th.validated = FALSE
                ORDER BY ce.trail_id, ST_Distance(ce.point, th.geom)
                ON CONFLICT DO NOTHING;
            """)

            # Aggiorna trail_count
            cur.execute("""
                UPDATE trailheads t
                SET trail_count = (
                    SELECT COUNT(*) FROM trail_trailhead tt WHERE tt.trailhead_id = t.id
                )
                WHERE validated = FALSE;
            """)

            conn.commit()

    finally:
        conn.close()

    logger.info(f'Trailhead draft generati: {n_trailheads}')
    return n_trailheads


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    compute_trailheads()
