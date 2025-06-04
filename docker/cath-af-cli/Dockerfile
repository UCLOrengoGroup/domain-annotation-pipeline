FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    wget \
    zlib1g-dev \
    make && \
    rm -rf /var/lib/apt/lists/*

# Install STRIDE
RUN mkdir -p /opt/stride && \
    cd /opt/stride && \
    wget --no-check-certificate https://webclu.bio.wzw.tum.de/stride/stride.tar.gz && \
    tar -zxf stride.tar.gz && \
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
