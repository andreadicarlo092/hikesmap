"""
Configurazione centralizzata — tutte le variabili d'ambiente in un unico posto.

Uso:
    from api.config import settings
    print(settings.database_url)

Le variabili vengono lette da .env in locale, da variabili di sistema in produzione.
Pydantic valida i tipi e solleva errori chiari se manca qualcosa di obbligatorio.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Ambiente
    env: str = Field(default="development", pattern="^(development|production|test)$")

    # Database — obbligatorio
    database_url: str = Field(
        ...,
        description="URL di connessione PostgreSQL (asyncpg). Non loggare mai questo valore."
    )

    # CORS — il frontend autorizzato a chiamare l'API
    cors_origins: str = Field(
        default="http://localhost:5173",
        description="URL del frontend, separati da virgola se multipli."
    )

    # Paginazione
    max_trails_per_request: int = Field(default=200, ge=1, le=1000)

    # Distanze di associazione ETL (in metri)
    shelter_search_radius_m: int = Field(
        default=150,
        description="Raggio entro cui cercare rifugi lungo il tracciato."
    )
    water_search_radius_m: int = Field(
        default=100,
        description="Raggio entro cui cercare fonti d'acqua lungo il tracciato."
    )
    parking_search_radius_m: int = Field(
        default=200,
        description="Raggio entro cui cercare parcheggi vicino al trailhead."
    )

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


# Istanza globale — importare questa, non istanziare Settings direttamente
settings = Settings()
