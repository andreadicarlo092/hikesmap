-- Trail Explorer MVP — Seed data (sviluppo / test)
-- Idempotente: usa ON CONFLICT DO NOTHING
-- Tutti i punti e geometrie sono nel Nord Italia (coordinate reali)

-- ============================================================
-- Trailheads (3 validati)
-- ============================================================
INSERT INTO trailheads (osm_id, name, trail_count, geom, source, validated)
VALUES
    (1001, 'Parcheggio Alpe Devero',        0,
     ST_SetSRID(ST_MakePoint(8.278, 46.302), 4326),  'manual', TRUE),
    (1002, 'Rifugio Gastaldi - Partenza',   0,
     ST_SetSRID(ST_MakePoint(8.464, 46.025), 4326),  'manual', TRUE),
    (1003, 'Piazza di Macugnaga',           0,
     ST_SetSRID(ST_MakePoint(7.965, 45.969), 4326),  'manual', TRUE)
ON CONFLICT DO NOTHING;

-- ============================================================
-- Trails (6 sentieri)
-- CAI duration formula: length_km/4 + elevation_gain_m/400
-- ============================================================

-- 1. Anello Alpe Devero (T) — 8 km, +450 m  → 2.0 + 1.125 = 3.1 h
INSERT INTO trails (osm_id, name, cai_ref, difficulty, network,
                    length_km, elevation_gain_m, elevation_loss_m,
                    duration_hours, tags, geom, geom_simplified_z8, geom_simplified_z12,
                    elevation_profile)
VALUES (
    2001,
    'Anello Alpe Devero',
    'AV2-01',
    'T',
    'hiking',
    8.2,
    450,
    450,
    3.1,
    '["circolare", "adatto famiglie"]'::jsonb,
    ST_GeomFromText(
        'LINESTRING(8.278 46.302, 8.283 46.308, 8.290 46.315,
                    8.298 46.318, 8.305 46.322, 8.310 46.318,
                    8.302 46.310, 8.295 46.304, 8.285 46.300, 8.278 46.302)',
        4326),
    ST_Simplify(ST_GeomFromText(
        'LINESTRING(8.278 46.302, 8.283 46.308, 8.290 46.315,
                    8.298 46.318, 8.305 46.322, 8.310 46.318,
                    8.302 46.310, 8.295 46.304, 8.285 46.300, 8.278 46.302)',
        4326), 0.005),
    ST_Simplify(ST_GeomFromText(
        'LINESTRING(8.278 46.302, 8.283 46.308, 8.290 46.315,
                    8.298 46.318, 8.305 46.322, 8.310 46.318,
                    8.302 46.310, 8.295 46.304, 8.285 46.300, 8.278 46.302)',
        4326), 0.002),
    '[{"d_km":0.0,"alt_m":1631},{"d_km":0.8,"alt_m":1680},{"d_km":1.6,"alt_m":1742},
      {"d_km":2.4,"alt_m":1810},{"d_km":3.2,"alt_m":1890},{"d_km":4.1,"alt_m":1980},
      {"d_km":5.0,"alt_m":1920},{"d_km":5.9,"alt_m":1810},{"d_km":6.8,"alt_m":1700},
      {"d_km":7.5,"alt_m":1650},{"d_km":8.2,"alt_m":1631}]'::jsonb
) ON CONFLICT (osm_id) DO NOTHING;

-- 2. Sentiero per il Passo di Crampiolo (E) — 6 km, +700 m → 1.5 + 1.75 = 3.25 h
INSERT INTO trails (osm_id, name, cai_ref, difficulty, network,
                    length_km, elevation_gain_m, elevation_loss_m,
                    duration_hours, tags, geom, geom_simplified_z8, geom_simplified_z12,
                    elevation_profile)
VALUES (
    2002,
    'Sentiero per il Passo di Crampiolo',
    'AV2-02',
    'E',
    'hiking',
    6.0,
    700,
    200,
    3.25,
    '["anello", "panoramico"]'::jsonb,
    ST_GeomFromText(
        'LINESTRING(8.278 46.302, 8.270 46.310, 8.263 46.320,
                    8.258 46.332, 8.252 46.345, 8.248 46.358,
                    8.243 46.370, 8.240 46.380)',
        4326),
    ST_Simplify(ST_GeomFromText(
        'LINESTRING(8.278 46.302, 8.270 46.310, 8.263 46.320,
                    8.258 46.332, 8.252 46.345, 8.248 46.358,
                    8.243 46.370, 8.240 46.380)',
        4326), 0.005),
    ST_Simplify(ST_GeomFromText(
        'LINESTRING(8.278 46.302, 8.270 46.310, 8.263 46.320,
                    8.258 46.332, 8.252 46.345, 8.248 46.358,
                    8.243 46.370, 8.240 46.380)',
        4326), 0.002),
    '[{"d_km":0.0,"alt_m":1631},{"d_km":0.6,"alt_m":1700},{"d_km":1.2,"alt_m":1790},
      {"d_km":1.8,"alt_m":1880},{"d_km":2.4,"alt_m":1970},{"d_km":3.0,"alt_m":2060},
      {"d_km":3.6,"alt_m":2150},{"d_km":4.2,"alt_m":2230},{"d_km":4.8,"alt_m":2280},
      {"d_km":5.4,"alt_m":2310},{"d_km":6.0,"alt_m":2331}]'::jsonb
) ON CONFLICT (osm_id) DO NOTHING;

-- 3. Alta Via Val Grande — Tratto Nord (EE) — 14 km, +1100 m → 3.5 + 2.75 = 6.25 h
INSERT INTO trails (osm_id, name, cai_ref, difficulty, network,
                    length_km, elevation_gain_m, elevation_loss_m,
                    duration_hours, tags, geom, geom_simplified_z8, geom_simplified_z12,
                    elevation_profile)
VALUES (
    2003,
    'Alta Via Val Grande - Tratto Nord',
    'AV3-01',
    'EE',
    'hiking',
    14.0,
    1100,
    600,
    6.25,
    '["alta quota", "panoramico"]'::jsonb,
    ST_GeomFromText(
        'LINESTRING(8.464 46.025, 8.452 46.038, 8.440 46.052,
                    8.430 46.068, 8.418 46.082, 8.405 46.096,
                    8.392 46.110, 8.380 46.124, 8.368 46.138,
                    8.355 46.150, 8.342 46.162, 8.330 46.172)',
        4326),
    ST_Simplify(ST_GeomFromText(
        'LINESTRING(8.464 46.025, 8.452 46.038, 8.440 46.052,
                    8.430 46.068, 8.418 46.082, 8.405 46.096,
                    8.392 46.110, 8.380 46.124, 8.368 46.138,
                    8.355 46.150, 8.342 46.162, 8.330 46.172)',
        4326), 0.005),
    ST_Simplify(ST_GeomFromText(
        'LINESTRING(8.464 46.025, 8.452 46.038, 8.440 46.052,
                    8.430 46.068, 8.418 46.082, 8.405 46.096,
                    8.392 46.110, 8.380 46.124, 8.368 46.138,
                    8.355 46.150, 8.342 46.162, 8.330 46.172)',
        4326), 0.002),
    '[{"d_km":0.0,"alt_m":680},{"d_km":1.4,"alt_m":820},{"d_km":2.8,"alt_m":980},
      {"d_km":4.2,"alt_m":1140},{"d_km":5.6,"alt_m":1300},{"d_km":7.0,"alt_m":1480},
      {"d_km":8.4,"alt_m":1620},{"d_km":9.8,"alt_m":1730},{"d_km":11.2,"alt_m":1780},
      {"d_km":12.6,"alt_m":1700},{"d_km":14.0,"alt_m":1580}]'::jsonb
) ON CONFLICT (osm_id) DO NOTHING;

-- 4. Cresta Ovest del Monte Rosa — Avvicinamento (EEA) — 9 km, +1200 m → 2.25 + 3.0 = 5.25 h
INSERT INTO trails (osm_id, name, cai_ref, difficulty, network,
                    length_km, elevation_gain_m, elevation_loss_m,
                    duration_hours, tags, geom, geom_simplified_z8, geom_simplified_z12,
                    elevation_profile)
VALUES (
    2004,
    'Cresta Ovest del Monte Rosa - Avvicinamento',
    'MR-01',
    'EEA',
    'hiking',
    9.0,
    1200,
    100,
    5.25,
    '{"surface":"scree","sac_scale":"alpine_hiking","foot":"yes","via_ferrata":"yes"}'::jsonb,
    ST_GeomFromText(
        'LINESTRING(7.965 45.969, 7.970 45.978, 7.976 45.990,
                    7.982 46.002, 7.988 46.015, 7.994 46.028,
                    7.999 46.042, 8.004 46.055, 8.008 46.068)',
        4326),
    ST_Simplify(ST_GeomFromText(
        'LINESTRING(7.965 45.969, 7.970 45.978, 7.976 45.990,
                    7.982 46.002, 7.988 46.015, 7.994 46.028,
                    7.999 46.042, 8.004 46.055, 8.008 46.068)',
        4326), 0.005),
    ST_Simplify(ST_GeomFromText(
        'LINESTRING(7.965 45.969, 7.970 45.978, 7.976 45.990,
                    7.982 46.002, 7.988 46.015, 7.994 46.028,
                    7.999 46.042, 8.004 46.055, 8.008 46.068)',
        4326), 0.002),
    '[{"d_km":0.0,"alt_m":1320},{"d_km":0.9,"alt_m":1480},{"d_km":1.8,"alt_m":1660},
      {"d_km":2.7,"alt_m":1850},{"d_km":3.6,"alt_m":2040},{"d_km":4.5,"alt_m":2230},
      {"d_km":5.4,"alt_m":2420},{"d_km":6.3,"alt_m":2180},{"d_km":7.2,"alt_m":2350},
      {"d_km":8.1,"alt_m":2480},{"d_km":9.0,"alt_m":2520}]'::jsonb
) ON CONFLICT (osm_id) DO NOTHING;

-- 5. Sentiero del Laghetto di Pianboglio (T) — 4.5 km, +280 m → 1.125 + 0.7 = 1.8 h
INSERT INTO trails (osm_id, name, cai_ref, difficulty, network,
                    length_km, elevation_gain_m, elevation_loss_m,
                    duration_hours, tags, geom, geom_simplified_z8, geom_simplified_z12,
                    elevation_profile)
VALUES (
    2005,
    'Sentiero del Laghetto di Pianboglio',
    'AV2-03',
    'T',
    'hiking',
    4.5,
    280,
    280,
    1.8,
    '["adatto famiglie", "panoramico"]'::jsonb,
    ST_GeomFromText(
        'LINESTRING(8.278 46.302, 8.282 46.307, 8.287 46.311,
                    8.292 46.315, 8.296 46.320, 8.300 46.325,
                    8.304 46.329)',
        4326),
    ST_Simplify(ST_GeomFromText(
        'LINESTRING(8.278 46.302, 8.282 46.307, 8.287 46.311,
                    8.292 46.315, 8.296 46.320, 8.300 46.325,
                    8.304 46.329)',
        4326), 0.005),
    ST_Simplify(ST_GeomFromText(
        'LINESTRING(8.278 46.302, 8.282 46.307, 8.287 46.311,
                    8.292 46.315, 8.296 46.320, 8.300 46.325,
                    8.304 46.329)',
        4326), 0.002),
    '[{"d_km":0.0,"alt_m":1631},{"d_km":0.45,"alt_m":1665},{"d_km":0.9,"alt_m":1710},
      {"d_km":1.35,"alt_m":1755},{"d_km":1.8,"alt_m":1790},{"d_km":2.25,"alt_m":1820},
      {"d_km":2.7,"alt_m":1840},{"d_km":3.15,"alt_m":1855},{"d_km":3.6,"alt_m":1870},
      {"d_km":4.05,"alt_m":1880},{"d_km":4.5,"alt_m":1885}]'::jsonb
) ON CONFLICT (osm_id) DO NOTHING;

-- 6. Traversata Rifugio Gastaldi — Bocchetta di Campo (E) — 18 km, +900 m → 4.5 + 2.25 = 6.75 h
INSERT INTO trails (osm_id, name, cai_ref, difficulty, network,
                    length_km, elevation_gain_m, elevation_loss_m,
                    duration_hours, tags, geom, geom_simplified_z8, geom_simplified_z12,
                    elevation_profile)
VALUES (
    2006,
    'Traversata Rifugio Gastaldi - Bocchetta di Campo',
    'AV3-02',
    'E',
    'hiking',
    18.0,
    900,
    1100,
    6.75,
    '["lungo", "alta quota"]'::jsonb,
    ST_GeomFromText(
        'LINESTRING(8.464 46.025, 8.478 46.018, 8.492 46.010,
                    8.506 46.000, 8.520 45.990, 8.534 45.978,
                    8.548 45.965, 8.562 45.952, 8.576 45.938,
                    8.590 45.924, 8.604 45.910, 8.618 45.895)',
        4326),
    ST_Simplify(ST_GeomFromText(
        'LINESTRING(8.464 46.025, 8.478 46.018, 8.492 46.010,
                    8.506 46.000, 8.520 45.990, 8.534 45.978,
                    8.548 45.965, 8.562 45.952, 8.576 45.938,
                    8.590 45.924, 8.604 45.910, 8.618 45.895)',
        4326), 0.005),
    ST_Simplify(ST_GeomFromText(
        'LINESTRING(8.464 46.025, 8.478 46.018, 8.492 46.010,
                    8.506 46.000, 8.520 45.990, 8.534 45.978,
                    8.548 45.965, 8.562 45.952, 8.576 45.938,
                    8.590 45.924, 8.604 45.910, 8.618 45.895)',
        4326), 0.002),
    '[{"d_km":0.0,"alt_m":680},{"d_km":1.8,"alt_m":760},{"d_km":3.6,"alt_m":870},
      {"d_km":5.4,"alt_m":1020},{"d_km":7.2,"alt_m":1180},{"d_km":9.0,"alt_m":1380},
      {"d_km":10.8,"alt_m":1520},{"d_km":12.6,"alt_m":1580},{"d_km":14.4,"alt_m":1480},
      {"d_km":16.2,"alt_m":1200},{"d_km":18.0,"alt_m":880}]'::jsonb
) ON CONFLICT (osm_id) DO NOTHING;

-- ============================================================
-- trail_trailhead — link sentieri ai trailhead
-- ============================================================

-- Trailhead 1 (Alpe Devero): trail 1, 2, 5
INSERT INTO trail_trailhead (trail_id, trailhead_id)
SELECT t.id, th.id
FROM trails t, trailheads th
WHERE t.osm_id IN (2001, 2002, 2005) AND th.osm_id = 1001
ON CONFLICT DO NOTHING;

-- Trailhead 2 (Rifugio Gastaldi): trail 3, 6
INSERT INTO trail_trailhead (trail_id, trailhead_id)
SELECT t.id, th.id
FROM trails t, trailheads th
WHERE t.osm_id IN (2003, 2006) AND th.osm_id = 1002
ON CONFLICT DO NOTHING;

-- Trailhead 3 (Macugnaga): trail 4
INSERT INTO trail_trailhead (trail_id, trailhead_id)
SELECT t.id, th.id
FROM trails t, trailheads th
WHERE t.osm_id = 2004 AND th.osm_id = 1003
ON CONFLICT DO NOTHING;

-- ============================================================
-- Aggiorna trail_count sui trailhead
-- ============================================================
UPDATE trailheads th
SET trail_count = (
    SELECT COUNT(*)
    FROM trail_trailhead tt
    WHERE tt.trailhead_id = th.id
);
