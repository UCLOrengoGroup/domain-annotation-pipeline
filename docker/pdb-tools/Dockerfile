FROM python:3.10-slim-buster

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         vim wget gzip tar git\
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY chop_pdbs.py chop_pdbs.py

RUN pip install --upgrade pip wheel pdb-tools

CMD ["/bin/bash"]