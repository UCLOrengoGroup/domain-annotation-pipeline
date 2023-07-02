FROM python:3.10-slim-buster

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         vim wget gzip tar git\
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ADD repo-key /
RUN \
  mkdir /root/.ssh && \
  chmod 600 /repo-key && \
  echo "IdentityFile /repo-key" >> /root/.ssh/ssh_config && \
  echo -e "StrictHostKeyChecking no" >> /root/.ssh/ssh_config && \
  git clone git://github.com/JudeWells/chainsaw

RUN pip install --upgrade pip wheel && pip install -r chainsaw/requirements.txt

RUN cd chainsaw/stride && tar -zxvf stride.tgz && make

CMD ["/bin/bash"]