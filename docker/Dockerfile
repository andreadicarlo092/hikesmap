# --- Stage 1: dipendenze ---
FROM python:3.11-slim AS builder

WORKDIR /build

# Installa solo quello che serve per compilare i pacchetti
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir --prefix=/install -r requirements.txt


# --- Stage 2: immagine finale ---
FROM python:3.11-slim

# Sicurezza: utente non-root
RUN useradd --no-create-home --shell /bin/false appuser

WORKDIR /app

# Copia le dipendenze compilate dallo stage precedente
COPY --from=builder /install /usr/local

# Copia il codice applicativo
COPY api/ ./api/

# Non copiare mai .env o file con segreti — le variabili arrivano dal runtime

# Permessi minimi: appuser è proprietario dei file
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Avvio in modalità produzione (1 worker per container — scalare con più repliche)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
