# Demo: Domain Annotation Pipeline

Data pipeline to provide consensus domain annotations for protein structures

## Install (with docker)

Install Nextflow

```
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install nextflow
```

Install Docker

https://docs.docker.com/compose/install/

Build Docker containers

```
docker compose build
```

## Run

```
nextflow run workflows/annotate.nf -c nextflow-with-docker.config
```
