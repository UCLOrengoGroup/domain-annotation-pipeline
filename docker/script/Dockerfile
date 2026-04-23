FROM python:3.10-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  vim wget gzip tar git procps unzip nodejs npm \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip wheel && pip install -r requirements.txt

ENV MOLSTAR_ROOT=/opt/molstar
ENV MOLSTAR_PREPROCESS_JS=/opt/molstar/node_modules/molstar/lib/commonjs/servers/model/preprocess.js

RUN npm install --prefix /opt/molstar molstar

COPY ./*.py ./

CMD ["/bin/bash"]