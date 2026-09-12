FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends tini ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 nally && mkdir -p /home/nally/workspace/projects /home/nally/workspace/files /home/nally/workspace/artifacts /home/nally/workspace/tmp /home/nally/workspace/.nallputer/state /workspace \
 && chown -R nally:nally /home/nally /workspace

WORKDIR /home/nally/workspace/projects

COPY nallputer/pyproject.toml /app/pyproject.toml
COPY nallputer/nallputer /app/nallputer
COPY nallputer/README.md /app/README.md

RUN pip install --no-cache-dir /app 2>&1 | tail -n 10

USER nally
ENV HOME=/home/nally \
    PYTHONUNBUFFERED=1 \
    PIP_NO_INPUT=1
EXPOSE 8000
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "nallputer.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
STOPSIGNAL SIGTERM
