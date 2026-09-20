-- Trail Explorer MVP — Schema PostgreSQL + PostGIS
-- Version: 1.0
-- Generated: 2026-09-20

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- ============================================================
-- trails
-- ============================================================
CREATE TABLE IF NOT EXISTS trails (
    id                      SERIAL PRIMARY KEY,
    osm_id                  BIGINT UNIQUE NOT NULL,
    osm_url                 TEXT GENERATED ALWAYS AS (
                                'https://www.openstreetmap.org/relation/' || osm_id
                            ) STORED,
    name                    TEXT,
    cai_ref                 TEXT,
    difficulty              VARCHAR(4),          -- T / E / EE / EEA
    network                 TEXT,                -- hiking / foot / bicycle
    length_km               FLOAT,
    elevation_gain_m        INT,
    elevation_loss_m        INT,
    duration_hours          FLOAT,               -- CAI formula: dist/4 + gain/400
    tags                    JSONB,
    geom                    GEOMETRY(LineString, 4326),
    geom_simplified_z8      GEOMETRY(LineString, 4326),
    geom_simplified_z12     GEOMETRY(LineString, 4326),
    elevation_profile       JSONB,               -- [{d_km, alt_m}, ...]
    imported_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- trailheads
-- ============================================================
CREATE TABLE IF NOT EXISTS trailheads (
    id          SERIAL PRIMARY KEY,
    osm_id      BIGINT,
    name        TEXT,
    trail_count INT NOT NULL DEFAULT 0,
    geom        GEOMETRY(Point, 4326),
    source      VARCHAR(20) NOT NULL DEFAULT 'auto_cluster',
    validated   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- trail_trailhead  (many-to-many join)
-- ============================================================
CREATE TABLE IF NOT EXISTS trail_trailhead (
    trail_id        INT NOT NULL REFERENCES trails(id)     ON DELETE CASCADE,
    trailhead_id    INT NOT NULL REFERENCES trailheads(id) ON DELETE CASCADE,
    PRIMARY KEY (trail_id, trailhead_id)
);

-- ============================================================
-- huts
-- ============================================================
CREATE TABLE IF NOT EXISTS huts (
    id      SERIAL PRIMARY KEY,
    osm_id  BIGINT UNIQUE NOT NULL,
    name    TEXT,
    geom    GEOMETRY(Point, 4326)
);

-- ============================================================
-- etl_run_log
-- ============================================================
CREATE TABLE IF NOT EXISTS etl_run_log (
    id                SERIAL PRIMARY KEY,
    started_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at      TIMESTAMPTZ,
    trails_imported   INT,
    trails_errors     INT,
    status            VARCHAR(20) NOT NULL DEFAULT 'running' -- running / success / error
);

-- ============================================================
-- etl_validation_log
-- ============================================================
CREATE TABLE IF NOT EXISTS etl_validation_log (
    id          SERIAL PRIMARY KEY,
    osm_id      BIGINT,
    issue       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Indexes
-- ============================================================

-- trails — spatial
CREATE INDEX IF NOT EXISTS idx_trails_geom
    ON trails USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_trails_geom_z8
    ON trails USING GIST (geom_simplified_z8);

-- trails — btree
CREATE INDEX IF NOT EXISTS idx_trails_difficulty
    ON trails (difficulty);

CREATE INDEX IF NOT EXISTS idx_trails_length
    ON trails (length_km);

CREATE INDEX IF NOT EXISTS idx_trails_elevation
    ON trails (elevation_gain_m);

-- trailheads — spatial
CREATE INDEX IF NOT EXISTS idx_trailheads_geom
    ON trailheads USING GIST (geom);

-- trailheads — btree
CREATE INDEX IF NOT EXISTS idx_trailheads_validated
    ON trailheads (validated);

-- huts — spatial
CREATE INDEX IF NOT EXISTS idx_huts_geom
    ON huts USING GIST (geom);

-- trail_trailhead — FK lookup
CREATE INDEX IF NOT EXISTS idx_trail_trailhead_th
    ON trail_trailhead (trailhead_id);
