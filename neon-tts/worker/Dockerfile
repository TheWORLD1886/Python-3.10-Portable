FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY tools/neon_tts.py character_voice_registry.json ./
COPY worker/app.py .
# neon_tts.py busca el registro en ../ ; dentro del contenedor está junto al código
ENV NEON_REGISTRY=/app/character_voice_registry.json
CMD exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}
