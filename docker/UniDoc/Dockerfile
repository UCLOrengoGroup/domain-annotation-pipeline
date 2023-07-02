FROM python:3.10-slim-buster

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         vim wget gzip tar git\
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN wget --no-check-certificate https://yanglab.nankai.edu.cn/UniDoc/download/UniDoc.tgz && tar xvf UniDoc.tgz

WORKDIR /app/UniDoc

CMD ["/bin/bash"]
