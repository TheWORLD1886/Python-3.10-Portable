#!/usr/bin/env bash
# Despliega el audio-worker en Google Cloud Run (nivel gratuito: escala a cero, sin GPU).
# Requisitos: gcloud autenticado y un proyecto con facturación habilitada (Cloud Run lo exige aunque no se cobre dentro del nivel gratuito).
set -euo pipefail
PROJECT=${PROJECT:?define PROJECT}; REGION=${REGION:-us-central1}
cd "$(dirname "$0")/.."
# 1) secreto del worker (se genera aquí y solo se guarda en Secret Manager; cópialo al gestor de credenciales de n8n)
if ! gcloud secrets describe neon-worker-token --project "$PROJECT" >/dev/null 2>&1; then
  python3 -c "import secrets;print(secrets.token_urlsafe(32),end='')" | gcloud secrets create neon-worker-token --data-file=- --project "$PROJECT"
fi
# 2) construir y desplegar (máx. 2 instancias, 0 mínimas = sin costo en reposo)
gcloud run deploy neon-audio-worker --source . --project "$PROJECT" --region "$REGION" \
  --set-secrets WORKER_TOKEN=neon-worker-token:latest --min-instances 0 --max-instances 2 \
  --cpu 1 --memory 1Gi --timeout 120 --allow-unauthenticated --quiet
echo "URL del worker:"; gcloud run services describe neon-audio-worker --project "$PROJECT" --region "$REGION" --format 'value(status.url)'
