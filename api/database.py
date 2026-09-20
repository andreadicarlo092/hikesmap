"""
Connessione al database PostgreSQL/PostGIS.

Usa un connection pool asincrono (asyncpg).
La URL di connessione viene letta da DATABASE_URL nelle variabili d'ambiente.
"""

import os
import asyncpg
import structlog

log = structlog.get_logger()

# Pool globale — inizializzato all'avvio dell'app, chiuso allo shutdown
_pool: asyncpg.Pool | None = None


async def connect() -> None:
    """Inizializza il connection pool. Chiamato all'avvio dell'app."""
    global _pool
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL non configurato")

    # Sicurezza: non loggare mai la URL (contiene username e password)
    log.info("db.connecting")
    _pool = await asyncpg.create_pool(
        dsn=database_url,
        min_size=2,
        max_size=10,
        command_timeout=30,
    )
    log.info("db.connected")


async def disconnect() -> None:
    """Chiude il connection pool. Chiamato allo shutdown dell'app."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        log.info("db.disconnected")


def get_pool() -> asyncpg.Pool:
    """Restituisce il pool attivo. Solleva eccezione se non inizializzato."""
    if _pool is None:
        raise RuntimeError("Database non connesso — chiamare connect() prima")
    return _pool
