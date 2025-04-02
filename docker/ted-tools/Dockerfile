FROM python:3.10-slim-buster

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  vim wget gzip tar git g++ \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/psipred/ted-tools.git /app/ted-tools

WORKDIR /app/ted-tools

RUN pip install --upgrade pip wheel && pip install -r /app/ted-tools/ted_consensus_1.0/requirements.txt

CMD [""]