# Demo: Domain Annotation Pipeline

Data pipeline to provide individual, combined and consensus filtered domain annotations for protein structures using Chainsaw, Merizo and UniDoc.

## Install (with docker)
Clone the repo.
https://github.com/UCLOrengoGroup/domain-annotation-pipeline

Install Nextflow
```
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install nextflow
```

Install Docker
https://docs.docker.com/compose/install/

Build Docker containers and run
```
docker compose build
docker-compose up -d
```

## Run
```
nextflow run workflows/annotate.nf -c nextflow-with-docker.config
```

# If the pipeline is to be installed and run on the HPC using Singularity rather than Docker, the following steps should be taken.

## Install (with singularity)
Clone the GitHub repository onto the server with git clone https://github.com/UCLOrengoGroup/domain-annotation-pipeline
Request access to the NextFlow shell askey, then activae with ssh askey

Set the following NextFlow environment variables interactively or add to ~/.bashrc.
```	
export NXF_OPTS='-Xms5g -Xmx5g'
export PATH=/share/apps/jdk-20.0.2/bin:$PATH
export LD_LIBRARY_PATH=/share/apps/jdk-20.0.2/lib:$LD_LIBRARY_PATH
export JAVA_HOME=/share/apps/jdk-20.0.2 
export PATH=/share/apps/genomics/nextflow-local-23.04.2:$PATH
```

Create a cache directory for NextFlow (not entirely necessary but will prevent warnings).
```
mkdir Scratch
mkdir Scratch/nextflow_singularity_cache 
export NXF_SINGULARITY_CACHEDIR=$HOME/Scratch/nextflow_singularity_cache
```

Set the following Python environment variables interactively or add to ~/.bashrc.
```
export PATH=/share/apps/python-3.13.0a6-shared/bin:$PATH
export LD_LIBRARY_PATH=/share/apps/python-3.13.0a6-shared/lib:$LD_LIBRARY_PATH
source /share/apps/source_files/python/python-3.13.0a6.source
```	

Set up the venv environment
```
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Follow the Install (with Docker) at the top of the page to install the workflow on a local computer.
Once Docker images have been built and are running, check their names and status.
```
docker images
```

This should return a list similar to the following:
domain-annotation-pipeline-chainsaw		latest	6f920fa32fc5	13GB
domain-annotation-pipeline-merizo		latest	1862bc2eed37	13.2GB
domain-annotation-pipeline-unidoc		latest	3676db5e232e	1.61GB
domain-annotation-pipeline-script		latest	b6af2bdac564	613MB
domain-annotation-pipeline-pdb-tools	latest	b1e301cc0fb9	369MB

If the images are not tagged with your Docker Docker username, tag each manually, check they are amd64 compatible and push each to DockerHub.
```
docker tag domain-annotation-pipeline-<image_name>:latest <username>/domain-annotation-pipeline-<image_name>:latest
docker inspect <username>/domain-annotation-pipeline-<image_name>:latest | grep Architecture
docker login
docker push <username>/domain-annotation-pipeline-<image_name>:latest
```

Go to the HPC server and pull each image to make singularity .sif files
```
singularity pull docker://<username>/domain-annotation-pipeline-<image_name>:latest
```

Locate and edit the nextflow-with-singularity.config file to update the executor (local or sge if to be used with qsub) and the path to your sif files. 
Save the config file to the domain-annotation-pipeline directory.

## Run from the domain-annoatation-pipeline directory.
```
nextflow run workflows/annotate.nf -c nextflow-with-singularity.config
```
