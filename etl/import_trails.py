import logging
import json
from typing import Optional

import osmium
from osmium.geom import WKBFactory
from shapely import wkb as shapely_wkb
from shapely.geometry import mapping, MultiLineString
from shapely.ops import linemerge
import psycopg2.extras

from config import FILTERED_PBF, BATCH_SIZE
from db import get_connection

logger = logging.getLogger(__name__)

DIFFICULTY_MAP = {
    'T': 'T', 'E': 'E', 'EE': 'EE', 'EEA': 'EEA',
    't': 'T', 'e': 'E', 'ee': 'EE', 'eea': 'EEA',
    '1': 'T', '2': 'E', '3': 'EE', '4': 'EEA',
}


class CAIRelationHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.ways = {}
        self.relations = []
        self._wkb = WKBFactory()

    def way(self, w):
        if w.is_closed() and len(w.nodes) < 4:
            return
        try:
            wkb = self._wkb.create_linestring(w)
            self.ways[w.id] = bytes.fromhex(wkb)
        except Exception:
            pass

    def relation(self, r):
        tags = {tag.k: tag.v for tag in r.tags}
        if tags.get('route') != 'hiking':
            return
        if not tags.get('cai_scale') and not tags.get('operator', '').upper().startswith('CAI'):
            return

        member_way_ids = [m.ref for m in r.members if m.type == 'w']
        if not member_way_ids:
            return

        extra_tags = {}
        for k in ('surface', 'trail_visibility', 'access', 'foot', 'bicycle', 'mtb'):
            if k in tags:
                extra_tags[k] = tags[k]

        self.relations.append({
            'osm_id': r.id,
            'name': tags.get('name') or tags.get('ref'),
            'cai_ref': tags.get('ref'),
            'difficulty': DIFFICULTY_MAP.get(tags.get('cai_scale', ''), None),
            'network': tags.get('network'),
            'tags': extra_tags,
            'member_way_ids': member_way_ids,
        })


def import_trails(pbf_path=FILTERED_PBF):
    logger.info('Lettura PBF con pyosmium...')
    handler = CAIRelationHandler()
    handler.apply_file(pbf_path, locations=True, idx='flex_mem')
    logger.info(f'Way caricate: {len(handler.ways)}, Relazioni trovate: {len(handler.relations)}')

    conn = get_connection()
    n_ok = 0
    n_err = 0

    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO etl_run_log (status) VALUES ('running') RETURNING id"
            )
            run_id = cur.fetchone()[0]
            conn.commit()

        for rel in handler.relations:
            try:
                way_geoms = []
                for way_id in rel['member_way_ids']:
                    wkb_bytes = handler.ways.get(way_id)
                    if wkb_bytes:
                        geom = shapely_wkb.loads(wkb_bytes)
                        way_geoms.append(geom)

                if not way_geoms:
                    raise ValueError('Nessuna way geometry trovata')

                if len(way_geoms) == 1:
                    merged = way_geoms[0]
                else:
                    merged = linemerge(MultiLineString(way_geoms))

                geojson_geom = json.dumps(mapping(merged))

                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO trails (
                            osm_id, name, cai_ref, difficulty, network, tags, geom
                        ) VALUES (
                            %(osm_id)s,
                            %(name)s,
                            %(cai_ref)s,
                            %(difficulty)s,
                            %(network)s,
                            %(tags)s::jsonb,
                            ST_SetSRID(ST_GeomFromGeoJSON(%(geom)s), 4326)
                        )
                        ON CONFLICT (osm_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            cai_ref = EXCLUDED.cai_ref,
                            difficulty = EXCLUDED.difficulty,
                            network = EXCLUDED.network,
                            tags = EXCLUDED.tags,
                            geom = EXCLUDED.geom,
                            updated_at = NOW()
                        RETURNING id
                    """, {
                        'osm_id': rel['osm_id'],
                        'name': rel['name'],
                        'cai_ref': rel['cai_ref'],
                        'difficulty': rel['difficulty'],
                        'network': rel['network'],
                        'tags': json.dumps(rel['tags']) if rel['tags'] else '{}',
                        'geom': geojson_geom,
                    })
                    trail_db_id = cur.fetchone()[0]

                    cur.execute("""
                        UPDATE trails SET
                            length_km = ROUND((ST_Length(geom::geography) / 1000.0)::numeric, 2),
                            duration_hours = ROUND(
                                (ST_Length(geom::geography) / 1000.0) / 4.0 +
                                COALESCE(elevation_gain_m, 0) / 400.0,
                            2)
                        WHERE id = %s
                    """, (trail_db_id,))

                    conn.commit()
                    n_ok += 1

            except Exception as e:
                conn.rollback()
                n_err += 1
                logger.warning(f'Errore sentiero osm_id={rel["osm_id"]}: {e}')
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO etl_validation_log (osm_id, issue) VALUES (%s, %s)",
                        (rel['osm_id'], str(e))
                    )
                    conn.commit()

        with conn.cursor() as cur:
            cur.execute("""
                UPDATE etl_run_log SET
                    completed_at = NOW(),
                    trails_imported = %s,
                    trails_errors = %s,
                    status = 'completed'
                WHERE id = %s
            """, (n_ok, n_err, run_id))
            conn.commit()

    finally:
        conn.close()

    logger.info(f'Import completato: {n_ok} OK, {n_err} errori')
    return n_ok, n_err


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    import_trails()
