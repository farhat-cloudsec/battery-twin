FROM python:3.11-slim

WORKDIR /app

RUN useradd --create-home appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ingest.py .

USER appuser

CMD ["python", "-u", "ingest.py"]