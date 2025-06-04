FROM python:3.10-slim-buster

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  vim wget gzip tar git\
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt
COPY ./*.py .

RUN pip install --upgrade pip wheel && pip install -r requirements.txt

CMD ["/bin/bash"]