FROM python:3.11-slim

WORKDIR /app

RUN useradd --create-home appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY twin.py .
COPY soh_model.joblib twin/soh_model.joblib

USER appuser

CMD ["python", "-u", "twin.py"]