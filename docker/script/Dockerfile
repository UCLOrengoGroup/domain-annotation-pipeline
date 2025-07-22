FROM python:3.10-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  vim wget gzip tar git procps \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip wheel && pip install -r requirements.txt

COPY ./*.py .

CMD ["/bin/bash"]