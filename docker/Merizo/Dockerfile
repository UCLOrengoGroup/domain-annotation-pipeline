FROM python:3.10-slim-buster

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  vim wget gzip tar git procps \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone https://github.com/psipred/Merizo

WORKDIR /app/Merizo

RUN pip install --upgrade pip wheel && pip install -r requirements.txt

CMD ["/bin/bash"]