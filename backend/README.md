# Trail Explorer API — Backend

FastAPI backend per Trail Explorer MVP. Espone sentieri CAI del Nord Italia via REST/GeoJSON.

## Stack

- **Python 3.11** + **FastAPI** + **asyncpg**
- **PostgreSQL 16** + **PostGIS 3.4**
- **Docker / Docker Compose v2**

## Setup locale (Docker)

### Prerequisiti

- Docker Desktop ≥ 24 o Docker Engine + Docker Compose v2
- Git

### Avvio

```bash
git clone https://github.com/andreadicarlo092/hikesmap.git
cd hikesmap
docker compose up --build
```

Al primo avvio, il container `db` esegue automaticamente `01_schema.sql` e `02_seed.sql`
(schema + dati di test con 6 sentieri realistici del Nord Italia).

| Servizio | URL |
|----------|-----|
| API docs (Swagger) | http://localhost:8000/docs |
| API ReDoc | http://localhost:8000/redoc |
| Frontend | http://localhost:3000 |
| Health check | http://localhost:8000/health |

---

## Endpoint disponibili

Tutti gli endpoint sono **read-only** (GET). Nessun endpoint di scrittura nell'MVP.

### Trailheads

#### `GET /api/v1/trailheads?bbox=<w,s,e,n>`

Restituisce i trailhead dentro il bounding box.

```bash
curl "http://localhost:8000/api/v1/trailheads?bbox=8.0,45.8,8.6,46.4"
```

Risposta: GeoJSON `FeatureCollection` con proprietà `id`, `name`, `osm_id`,
`lat`, `lon`, `trail_count`, `validated`.

Parametri:
- `bbox` (obbligatorio): `west,south,east,north` in WGS84
- `limit` (opzionale, default 500, max 2000)

#### `GET /api/v1/trailheads/{id}`

Dettaglio trailhead singolo.

```bash
curl "http://localhost:8000/api/v1/trailheads/1"
```

#### `GET /api/v1/trailheads/{id}/trails`

Lista sentieri che partono da questo trailhead, ordinati per difficoltà poi lunghezza.

```bash
curl "http://localhost:8000/api/v1/trailheads/1/trails"
```

---

### Trails

#### `GET /api/v1/trails/{id}`

Sentiero completo come GeoJSON Feature (geometria `LineString`).

```bash
curl "http://localhost:8000/api/v1/trails/2001"
```

Proprietà restituite: `id`, `osm_id`, `name`, `cai_scale`, `length_km`,
`elevation_gain_m`, `elevation_loss_m`, `duration_min`, `surface`, `osm_url`.

#### `GET /api/v1/trails/{id}/elevation`

Profilo altimetrico del sentiero.

```bash
curl "http://localhost:8000/api/v1/trails/2001/elevation"
```

Risposta: `{ trail_id, samples: [{distance_m, altitude_m}, ...], gain_m, loss_m, max_alt_m, min_alt_m }`.

#### `GET /api/v1/trails/{id}/gpx`

Scarica il GPX del sentiero.

```bash
curl -O "http://localhost:8000/api/v1/trails/2001/gpx"
```

Restituisce un file `sentiero_2001.gpx` (GPX 1.1).

---

## Schema DB (riassunto)

| Tabella | Descrizione |
|---------|-------------|
| `trails` | Sentieri con geometria PostGIS, profilo altimetrico JSONB, attributi CAI |
| `trailheads` | Punti di partenza con coordinate PostGIS |
| `trail_trailhead` | Associazione N:N sentieri ↔ trailhead |
| `huts` | Rifugi (non esposti nell'MVP) |
| `etl_run_log` | Log delle esecuzioni ETL |
| `etl_validation_log` | Errori di validazione ETL |

Schema completo: `backend/sql/schema.sql`

---

## Variabili d'ambiente

Copia `.env.example` in `.env` per l'avvio locale senza Docker:

```bash
cp backend/.env.example backend/.env
```

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://trail:trail@db:5432/trailexplorer` | DSN asyncpg |
| `DATABASE_URL_SYNC` | `postgresql://trail:trail@db:5432/trailexplorer` | DSN sincrono (Alembic) |
| `DEBUG` | `false` | Abilita log debug |
| `CORS_ORIGINS` | `["http://localhost:3000","http://localhost:5173"]` | Origini CORS ammesse |

---

## Seed data

Il file `backend/sql/seed.sql` carica 3 trailhead e 6 sentieri realistici
(Alpe Devero, Rifugio Gastaldi, Macugnaga) per testare l'API senza eseguire l'ETL.

Per aggiungere altri sentieri di test, aggiungi blocchi `INSERT INTO trails ... ON CONFLICT DO NOTHING`
seguiti da `INSERT INTO trail_trailhead ...`.

---

## Sviluppo senza Docker

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Assicurarsi che DATABASE_URL punti a un PostgreSQL+PostGIS locale
uvicorn app.main:app --reload
```

---

## Struttura del progetto

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py          # Settings (pydantic-settings)
│   ├── database.py        # Pool asyncpg + dipendenza get_db
│   ├── main.py            # App FastAPI, lifespan, CORS, router include
│   ├── models.py          # Modelli Pydantic v2 (GeoJSON response)
│   └── routers/
│       ├── __init__.py
│       ├── trailheads.py  # /api/v1/trailheads
│       └── trails.py      # /api/v1/trails
├── sql/
│   ├── schema.sql         # DDL completo (tabelle + indici PostGIS)
│   └── seed.sql           # Dati di test
├── .dockerignore
├── .env.example
├── Dockerfile
├── pyproject.toml
└── requirements.txt
docker-compose.yml          # Tutti i servizi (db, api, frontend, nginx commentato)
```
