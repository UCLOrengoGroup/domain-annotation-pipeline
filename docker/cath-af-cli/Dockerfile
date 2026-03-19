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

# Clone cath-alphaflow repository
RUN git clone https://github.com/UCLOrengoGroup/cath-alphaflow.git

# Install Python dependencies and cath-alphaflow
RUN pip install --upgrade pip wheel && \
    pip install -e /app/cath-alphaflow

# Default command
CMD ["cath-af-cli"]
