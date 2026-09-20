# hikesmap

Mappa interattiva di sentieri escursionistici del Nord Italia, con dati OpenStreetMap, profili altimetrici e ricerca per difficoltà.

## Stack

| Layer | Tecnologia |
|---|---|
| Frontend | SvelteKit + MapLibre GL JS |
| Backend API | FastAPI (Python) |
| Database | PostgreSQL + PostGIS |
| Tile map | PMTiles su CDN (Cloudflare R2) |
| ETL | Python (OSM + DEM Copernicus) |
| Infra | Railway (API + DB) · Vercel (Frontend) |

## Struttura del progetto

```
hikesmap/
├── etl/          # Scarica e processa dati OSM e DEM
├── api/          # Backend FastAPI
├── frontend/     # App SvelteKit (mappa)
├── docs/         # Documentazione tecnica
├── docker/       # Configurazione container
└── .github/
    └── workflows/ # CI/CD
```

## Come avviare in locale

> Prerequisiti: Python 3.11+, Node.js 20+, Docker

```bash
# 1. Clona la repo
git clone https://github.com/andreadicarlo092/hikesmap.git
cd hikesmap

# 2. Avvia il database
docker compose -f docker/docker-compose.yml up -d db

# 3. Avvia l'API
cd api
cp .env.example .env  # configura le variabili
pip install -r requirements.txt
uvicorn main:app --reload

# 4. Avvia il frontend
cd frontend
npm install
npm run dev
```

## Licenza

[AGPL-3.0](LICENSE)
