# Boon-Tube-Daemon Docker Image
# Python 3.14 with multi-arch support: amd64, arm64
#
# Security fixes:
# - CVE-2025-7709: SQLite upgraded to 3.50.4 (from 3.46.1)
# - CVE-2025-8869: pip upgraded to 25.3+ (symbolic link extraction)
# The base image is pinned by digest so a rebuild is reproducible and a
# retagged upstream image cannot slip in; Dependabot moves the digest.
FROM python:3.14-slim@sha256:caaf356f40667c496d405780745b9ac25771c189a51dfcc42430d531ea09f8a2

# Set build arguments for platform detection (automatically set by buildx)
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Set working directory
WORKDIR /app

# Install system dependencies and upgrade packages
# CVE-2025-7709: SQLite FTS5 integer overflow (fixed in 3.50.3+)
# Note: Python's built-in sqlite3 uses the system SQLite which is 3.46.1
# We'll install pysqlite3-binary which bundles SQLite 3.50.4+
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create and activate virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
# Upgrade pip to 25.3+ to fix CVE-2025-8869 (symbolic link extraction vulnerability)
RUN pip install --no-cache-dir --upgrade "pip>=25.3" && \
    pip install --no-cache-dir --require-hashes -r requirements.txt

# Drop pip from the runtime image once the dependencies are in place. Nothing
# runs pip after this point, and pip vendors its own copies of msgpack
# (GHSA-6v7p-g79w-8964) and setuptools' pkg_resources (CVE-2025-47273,
# CVE-2026-59890) that Trivy reports from pip/_vendor/bom.cdx.json; the venv
# itself carries neither package, so upgrading them there changes nothing.
# `python -m ensurepip` restores pip if a shell session ever needs it.
RUN python -m pip uninstall -y pip && \
    /usr/local/bin/python -m pip uninstall -y pip

# Copy application code
COPY boon_tube_daemon/ /app/boon_tube_daemon/
COPY main.py /app/

# Create config directory
RUN mkdir -p /app/config

# Expose volume for configuration
VOLUME ["/app/config"]

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check: probe the daemon's /healthz endpoint (hypeman-social
# observability) when HEALTH_PORT is set; otherwise fall back to verifying
# PID 1 is alive so the check passes for deployments that keep health off.
# Uses python urllib because slim images ship neither curl nor pgrep.
HEALTHCHECK --interval=5m --timeout=5s --start-period=60s --retries=3 \
  CMD ["python", "-c", "import os,sys,urllib.request;port=os.getenv('HEALTH_PORT');urllib.request.urlopen(f'http://127.0.0.1:{port}/healthz', timeout=4) if port else sys.exit(0 if os.path.isdir('/proc/1') else 1)"]

# Run the daemon
CMD ["python", "-u", "main.py"]
