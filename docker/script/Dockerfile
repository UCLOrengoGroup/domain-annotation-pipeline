FROM python:3.10-slim-buster

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  vim wget gzip tar git\
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt
COPY convert_merizo_unidoc_files.py convert_merizo_unidoc_files.py
COPY combine_results.py combine_results.py
COPY transform_consensus.py transform_consensus.py
COPY transform_consensus_2.py transform_consensus_2.py

RUN pip install --upgrade pip wheel && pip install -r requirements.txt

CMD ["/bin/bash"]