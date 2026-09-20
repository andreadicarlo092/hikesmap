# Trail Explorer — ETL Pipeline

Pipeline di importazione dati OSM → PostGIS per Trail Explorer.

## Prerequisiti

- Docker e Docker Compose
- Il servizio `db` deve essere in esecuzione (avviato con `docker compose up db`)

## Avvio pipeline completa (Piemonte)

```bash
docker compose --profile etl run etl
```

Questo comando:
1. Scarica il dump OSM del Nord Ovest Italia da Geofabrik (~700 MB)
2. Filtra con `osmium` le relazioni route=hiking con tag CAI
3. Importa i sentieri in PostgreSQL con pyosmium
4. Calcola i trailhead automatici con ST_ClusterDBSCAN
5. Calcola le geometrie LOD (zoom 8 e 12)

**Prima esecuzione:** il download può richiedere 10-30 minuti a seconda della connessione. Le esecuzioni successive saltano il download se il .pbf è già presente nel volume `etl_data`.

## Validazione trailhead

Dopo la pipeline, i trailhead generati automaticamente sono in stato **draft** (`validated=FALSE`) e non vengono esposti dall'API. Vanno validati manualmente:

```bash
# Mostra i draft in attesa
docker compose --profile etl run etl python validate_cli.py list

# Approva tutti (per test rapido)
docker compose --profile etl run etl python validate_cli.py approve-all

# Approva singolo
docker compose --profile etl run etl python validate_cli.py approve 42

# Statistiche DB
docker compose --profile etl run etl python validate_cli.py stats
```

## Profili altimetrici (richiede DEM Copernicus)

I profili altimetrici non sono generati dalla pipeline base — richiedono il DEM Copernicus GLO-30 (~2 GB per il Nord Italia). Vedi la sezione **DEM** del README principale per le istruzioni di download e caricamento in PostGIS.

## Struttura file

```
etl/
  main.py           # Entry point pipeline completa
  download.py       # Download Geofabrik + filtro osmium
  import_trails.py  # Import pyosmium -> PostGIS
  trailheads.py     # Algoritmo ST_ClusterDBSCAN
  lod.py            # Geometrie semplificate LOD
  validate_cli.py   # CLI validazione trailhead
  config.py         # Configurazione da env
  db.py             # Helper connessione PostgreSQL
  Dockerfile        # Container Python + osmium-tool
  requirements.txt  # Dipendenze Python
```

## Variabili d'ambiente

| Variabile | Default | Descrizione |
|---|---|---|
| `DB_HOST` | `db` | Host PostgreSQL |
| `DB_PORT` | `5432` | Porta PostgreSQL |
| `DB_NAME` | `trailexplorer` | Nome database |
| `DB_USER` | `trailexplorer` | Utente database |
| `DB_PASSWORD` | `trailexplorer` | Password database |
| `ETL_REGION` | `piemonte` | Regione da importare |
| `ETL_DATA_DIR` | `/tmp/etl_data` | Directory dati temporanei |
