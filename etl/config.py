import os
from dotenv import load_dotenv

load_dotenv()

# Database
DB_HOST = os.getenv('DB_HOST', 'db')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME', 'trailexplorer')
DB_USER = os.getenv('DB_USER', 'trailexplorer')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'trailexplorer')

# OSM / Geofabrik
GEOFABRIK_BASE = 'https://download.geofabrik.de'
REGIONS = {
    'piemonte': f'{GEOFABRIK_BASE}/europe/italy/nord-ovest-latest.osm.pbf',
}
# Regione pilota MVP
DEFAULT_REGION = os.getenv('ETL_REGION', 'piemonte')

# Percorsi file
DATA_DIR = os.getenv('ETL_DATA_DIR', '/tmp/etl_data')
RAW_PBF = os.path.join(DATA_DIR, 'region_raw.osm.pbf')
FILTERED_PBF = os.path.join(DATA_DIR, 'cai_routes.osm.pbf')

# Clustering trailhead
CLUSTER_EPS_DEG = 0.0005  # ~50m a 45 lat
CLUSTER_MIN_SAMPLES = 1

# ETL behavior
BATCH_SIZE = int(os.getenv('ETL_BATCH_SIZE', '500'))
