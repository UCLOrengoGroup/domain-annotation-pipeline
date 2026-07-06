FROM python:3.10-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  vim wget gzip tar git procps zip unzip nodejs npm \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# NOTE: build context is the repository root (see docker-compose.yml), so paths
# below are relative to the repo root, not to docker/script/.
COPY docker/script/requirements.txt requirements.txt

RUN pip install --upgrade pip wheel && pip install -r requirements.txt

ENV MOLSTAR_ROOT=/opt/molstar
ENV MOLSTAR_PREPROCESS_JS=/opt/molstar/node_modules/molstar/lib/commonjs/servers/model/preprocess.js

RUN npm install --prefix /opt/molstar molstar

# Pipeline scripts live in workflows/bin/ (= ${projectDir}/bin for the
# workflows/annotate.nf entry point). Install them onto PATH so they resolve by
# bare name, matching the ${projectDir}/bin-on-PATH mechanism Nextflow uses at runtime.
COPY workflows/bin/*.py /usr/local/bin/
RUN chmod +x /usr/local/bin/*.py

CMD ["/bin/bash"]