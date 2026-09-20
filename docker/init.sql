-- hikesmap — schema database
-- Eseguito automaticamente da PostGIS al primo avvio del container.
-- Richiede estensione PostGIS (inclusa nell'immagine postgis/postgis).

-- Estensioni
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- ---------------------------------------------------------------------------
-- Utenti DB con permessi minimi
-- L'ETL (scrittura) e l'API (sola lettura) usano utenti separati.
-- Le password vengono impostate tramite variabili d'ambiente nel deploy.
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'hikesmap_etl') THEN
        CREATE ROLE hikesmap_etl LOGIN PASSWORD 'CHANGEME_ETL';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'hikesmap_api') THEN
        CREATE ROLE hikesmap_api LOGIN PASSWORD 'CHANGEME_API';
    END IF;
END $$;


-- ---------------------------------------------------------------------------
-- Tabella principale: sentieri
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trails (
    id              BIGSERIAL PRIMARY KEY,
    osm_id          BIGINT NOT NULL UNIQUE,         -- ID way OpenStreetMap
    name            TEXT,                           -- tag name=*
    ref             TEXT,                           -- tag ref=* (es. "GTA", "101")
    difficulty      TEXT,                           -- T1..T6 (mappato da sac_scale=*)
    surface         TEXT,                           -- tag surface=*
    distance_m      INTEGER,                        -- calcolato dalla geometria
    elevation_gain_m  INTEGER,                      -- da DEM Copernicus
    elevation_loss_m  INTEGER,
    elevation_min_m   INTEGER,
    elevation_max_m   INTEGER,
    region          TEXT,                           -- reverse geocoding sul trailhead
    trailhead_name  TEXT,                           -- nodo OSM più vicino all'inizio
    water_at_start  BOOLEAN,                        -- NULL = sconosciuto
    updated_at      TIMESTAMPTZ,                    -- timestamp OSM del way

    -- Geometria (SRID 4326 = WGS84 — standard GPS)
    geometry        GEOMETRY(LineString, 4326) NOT NULL,
    trailhead       GEOMETRY(Point, 4326),          -- primo punto del tracciato

    -- Bbox precalcolata per query veloci
    bbox_min_lon    FLOAT,
    bbox_min_lat    FLOAT,
    bbox_max_lon    FLOAT,
    bbox_max_lat    FLOAT,

    -- Metadati interni
    imported_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_internal_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indici spaziali (fondamentali per le query per area geografica)
CREATE INDEX IF NOT EXISTS trails_geometry_idx  ON trails USING GIST(geometry);
CREATE INDEX IF NOT EXISTS trails_trailhead_idx ON trails USING GIST(trailhead);

-- Indici su campi filtro frequenti
CREATE INDEX IF NOT EXISTS trails_difficulty_idx ON trails(difficulty);
CREATE INDEX IF NOT EXISTS trails_region_idx     ON trails(region);
CREATE INDEX IF NOT EXISTS trails_osm_id_idx     ON trails(osm_id);


-- ---------------------------------------------------------------------------
-- Tabella: rifugi alpini
-- Popolata dall'ETL da tourism=alpine_hut in OSM.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS shelters (
    id              BIGSERIAL PRIMARY KEY,
    osm_id          BIGINT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    elevation_m     INTEGER,
    opening_hours   TEXT,
    capacity        INTEGER,
    location        GEOMETRY(Point, 4326) NOT NULL,
    imported_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS shelters_location_idx ON shelters USING GIST(location);


-- ---------------------------------------------------------------------------
-- Tabella: fonti d'acqua
-- Popolata dall'ETL da amenity=drinking_water in OSM.
-- ATTENZIONE: copertura lacunosa — NULL non equivale ad assenza.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS water_sources (
    id              BIGSERIAL PRIMARY KEY,
    osm_id          BIGINT NOT NULL UNIQUE,
    name            TEXT,
    location        GEOMETRY(Point, 4326) NOT NULL,
    imported_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS water_sources_location_idx ON water_sources USING GIST(location);


-- ---------------------------------------------------------------------------
-- Tabella: parcheggi
-- Popolata dall'ETL da amenity=parking in OSM.
-- ATTENZIONE: associazione con trailhead basata su prossimità — inaffidabile.
-- Valutare integrazione con fonti CAI o contributi utenti.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS parkings (
    id              BIGSERIAL PRIMARY KEY,
    osm_id          BIGINT NOT NULL UNIQUE,
    name            TEXT,
    notes           TEXT,                           -- inserito manualmente
    location        GEOMETRY(Point, 4326) NOT NULL,
    imported_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS parkings_location_idx ON parkings USING GIST(location);


-- ---------------------------------------------------------------------------
-- Tabella di join: sentieri <-> rifugi (M:N)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trail_shelters (
    trail_id        BIGINT REFERENCES trails(id)   ON DELETE CASCADE,
    shelter_id      BIGINT REFERENCES shelters(id) ON DELETE CASCADE,
    distance_from_trail_m INTEGER,                 -- distanza del rifugio dal tracciato
    PRIMARY KEY (trail_id, shelter_id)
);


-- ---------------------------------------------------------------------------
-- Tabella di join: sentieri <-> fonti d'acqua (M:N)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trail_water_sources (
    trail_id        BIGINT REFERENCES trails(id)         ON DELETE CASCADE,
    water_source_id BIGINT REFERENCES water_sources(id)  ON DELETE CASCADE,
    distance_from_trail_m INTEGER,
    PRIMARY KEY (trail_id, water_source_id)
);


-- ---------------------------------------------------------------------------
-- Tabella di join: sentieri <-> parcheggi (M:N)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trail_parkings (
    trail_id        BIGINT REFERENCES trails(id)   ON DELETE CASCADE,
    parking_id      BIGINT REFERENCES parkings(id) ON DELETE CASCADE,
    distance_from_trailhead_m INTEGER,
    PRIMARY KEY (trail_id, parking_id)
);


-- ---------------------------------------------------------------------------
-- Permessi: API legge tutto, ETL scrive tutto
-- ---------------------------------------------------------------------------
GRANT SELECT ON ALL TABLES IN SCHEMA public TO hikesmap_api;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO hikesmap_etl;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO hikesmap_etl;
