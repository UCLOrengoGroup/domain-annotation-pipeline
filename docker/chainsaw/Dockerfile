FROM python:3.10-slim-buster

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  vim wget gzip tar git g++ make \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone https://github.com/JudeWells/chainsaw

RUN pip install --upgrade pip wheel && pip install -r chainsaw/requirements.txt

RUN cd chainsaw/stride && tar -zxvf stride.tgz && make

CMD ["/bin/bash"]

