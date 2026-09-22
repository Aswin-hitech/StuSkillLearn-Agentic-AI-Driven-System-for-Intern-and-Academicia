FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system stuskill && adduser --system --ingroup stuskill --home /app stuskill

COPY requirements.txt requirements-integrations.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-integrations.txt

COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
COPY pyproject.toml ./

RUN chown -R stuskill:stuskill /app
USER stuskill

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=3)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
