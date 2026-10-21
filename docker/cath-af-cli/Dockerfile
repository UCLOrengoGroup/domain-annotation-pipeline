FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    unzip \
    wget \
    procps \
    zlib1g-dev \
    make && \
    rm -rf /var/lib/apt/lists/*

# Install STRIDE
RUN mkdir -p /opt/stride && \
    cd /opt/stride && \
    wget https://github.com/heiniglab/stride/archive/refs/heads/main.zip && \
    unzip main.zip && \
    cd stride-main && \
    make && \
    cp stride /usr/local/bin/stride

# Set up app directory
WORKDIR /app

# Install the centrally pinned cath-alphaflow release.
COPY conf/dependencies.config /tmp/dependencies.config
RUN CATH_ALPHAFLOW_VERSION="$(sed -n "s/^[[:space:]]*cath_alphaflow_version[[:space:]]*=[[:space:]]*['\"]\\([^'\"]*\\)['\"].*/\\1/p" /tmp/dependencies.config)" \
    && test -n "${CATH_ALPHAFLOW_VERSION}" \
    && git clone --depth 1 https://github.com/UCLOrengoGroup/cath-alphaflow.git \
        --branch "${CATH_ALPHAFLOW_VERSION}" /app/cath-alphaflow

# Install Python dependencies and cath-alphaflow
RUN pip install --upgrade pip wheel && \
    pip install -e /app/cath-alphaflow

# Default command
CMD ["cath-af-cli"]
