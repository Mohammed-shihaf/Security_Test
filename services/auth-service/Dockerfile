# syntax=docker/dockerfile:1.7
FROM python:3.12-slim-bookworm AS deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim-bookworm AS runner
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PORT=8001
RUN apt-get update \
  && apt-get install -y --no-install-recommends wget \
  && rm -rf /var/lib/apt/lists/* \
  && useradd -m -u 1001 appuser

COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY app ./app

USER appuser
EXPOSE 8001
CMD sh -c 'exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}'
