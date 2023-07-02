FROM python:3.10-slim-buster

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         vim wget gzip tar git\
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone https://github.com/UCLOrengoGroup/cath-alphaflow

RUN pip install --upgrade pip wheel && pip install -e /app/cath-alphaflow

CMD ["cath-af-cli"]