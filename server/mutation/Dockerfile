# Image for running the tests and Cosmic Ray. Uses Linux like our server.
# Has the project dependencies + pytest + Cosmic Ray.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8

RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --root-user-action=ignore \
    "PyMuPDF>=1.21.1" Flask==3.0.3 PyMySQL==1.1.2 SQLAlchemy==2.0.43 dill==0.4.0 \
    "rmap @ git+https://github.com/nharrand/RMAP.git@v1.0.2" \
    pytest pytest-cov "hypothesis>=6.0.0" cosmic-ray==8.4.3

WORKDIR /work
