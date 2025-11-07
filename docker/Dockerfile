# Boon-Tube-Daemon Docker Image
# Python 3.14 with multi-arch support: amd64, arm64
#
# NOTE: This build excludes TikTok/Playwright dependencies to reduce image size
# and eliminate browser-related vulnerabilities. TikTok support is planned but
# not yet functional. When TikTok is ready, switch to requirements.txt (full build).
#
# Security fixes:
# - CVE-2025-7709: SQLite upgraded to 3.50.4 (from 3.46.1)
# - CVE-2025-8869: pip upgraded to 25.3+ (symbolic link extraction)
FROM python:3.14-slim

# Set build arguments for platform detection (automatically set by buildx)
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Set working directory
WORKDIR /app

# Install system dependencies and upgrade SQLite to fix CVE-2025-7709
# CVE-2025-7709: Integer overflow in SQLite FTS5 extension (fixed in 3.50.3)
# Debian trixie ships 3.46.1-7, so we compile SQLite 3.50.4 from source
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    wget \
    make \
    tcl \
    && cd /tmp \
    && wget https://www.sqlite.org/2025/sqlite-autoconf-3500400.tar.gz \
    && tar xzf sqlite-autoconf-3500400.tar.gz \
    && cd sqlite-autoconf-3500400 \
    && ./configure --prefix=/usr --enable-fts5 \
    && make -j$(nproc) \
    && make install \
    && ldconfig \
    && cd / \
    && rm -rf /tmp/sqlite-autoconf-3500400* \
    && apt-get purge -y wget make tcl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements first for better caching (without TikTok/Playwright dependencies)
COPY docker/requirements-no-tiktok.txt /app/requirements.txt

# Install Python dependencies
# Upgrade pip to 25.3+ to fix CVE-2025-8869 (symbolic link extraction vulnerability)
RUN pip install --no-cache-dir --upgrade "pip>=25.3" && \
    pip install --no-cache-dir -r requirements.txt

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

# Health check
HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "import boon_tube_daemon; print('OK')" || exit 1

# Run the daemon
CMD ["python", "-u", "main.py"]
