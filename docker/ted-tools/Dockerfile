FROM python:3.10-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  vim make wget gzip tar git g++ procps \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# RUN git clone https://github.com/psipred/ted-tools.git /app/ted-tools
RUN git clone https://github.com/sillitoe/ted-tools.git /app/ted-tools

WORKDIR /app/ted-tools/ted_consensus_1.0

RUN bash setup.sh

CMD ["/bin/bash"]