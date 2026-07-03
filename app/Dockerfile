# NOTE: this Dockerfile is for local testing only. Streamlit Community
# Cloud (the actual hosting target) builds and runs the app directly from
# source + requirements.txt — it does not use this Dockerfile at all.
FROM python:3.12-slim

WORKDIR /app

# Install the shared domain package first (better layer caching —
# app deps change more often than the domain package).
COPY common /tmp/common
RUN pip install --no-cache-dir /tmp/common && rm -rf /tmp/common

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/dashboard.py .

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
