FROM python:3.11-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  vim wget gzip tar git procps zip unzip \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY chop_pdbs.py chop_pdbs.py

RUN pip install --upgrade pip wheel pdb-tools

CMD ["/bin/bash"]