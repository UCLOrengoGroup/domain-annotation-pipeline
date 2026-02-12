FROM python:3.10-slim
# FROM pytorch/pytorch:

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  vim make wget gzip tar git g++ procps zip unzip rsync \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# RUN git clone https://github.com/psipred/ted-tools.git /app/ted-tools
ARG CACHE_BUST=3
RUN git clone --depth 1 https://github.com/sillitoe/ted-tools.git --branch v0.1.1 /app/ted-tools

WORKDIR /app/ted-tools/ted_consensus_1.0

RUN bash setup.sh && python3 -m pip cache purge

# If we want to use the old UniDoc executables
# RUN TED_VERSION=1.0 bash setup.sh

CMD ["/bin/bash"]