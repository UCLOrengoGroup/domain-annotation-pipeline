FROM python:3.10

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  vim wget gzip tar git\
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN wget --no-check-certificate http://yanglab.qd.sdu.edu.cn/UniDoc/download/UniDoc.tgz && tar xvf UniDoc.tgz

WORKDIR /app/UniDoc

# unidoc expects to find all the executables in the current directory
RUN cp bin/* . && rm -rf bin

ENV PATH="$PATH:."

CMD ["/bin/bash"]
