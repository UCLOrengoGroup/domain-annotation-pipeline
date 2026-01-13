# Domain Annotation Pipeline

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

```bash
docker compose build
```

## Running the workflow

The following runs the `debug` mode, which uses test data included in this repository.
Note: either docker or singularity must be supplied as one the the profile arguments.

```
nextflow run workflows/annotate.nf -profile debug,docker
```

## Preparing data

The pipeline expects two inputs:

- a zip file containing PDB files
- a file containing all the ids that should be processed

Given the following directory:

```bash
pdb_files/A0A3G5A0R2.pdb
pdb_files/A0A8S5U119.pdb
pdb_files/A0A0B5IZ33.pdb
pdb_files/UPI001E716444.pdb
pdb_files/A0A6C0N656.pdb
```

Create a zip file from all PDB files in this directory:

```bash
cd pdb_files
zip -r ../pdb_files.zip .
```

Create a file containing all the ids to process:

```bash
# list the files in the zip and remove the `.pdb` suffix
zipinfo -1 pdb_files.zip | sed 's/.pdb//g' > ids.txt
```

Pass these parameters to nextflow:

```bash
nextflow run workflows/annotate.nf \
    --pdb_zip_file pdb_files.zip \
    --uniprot_csv_file ids.txt \
    -profile debug,docker
```
Also useful to note:
The output directory can be controlled with the ```--project_name``` parameter. 
The three chunk size parameters control how many IDs are processed concurrently at different stages of the workflow:

```bash
--chunk_size
--light_chunk_size
--heavy_chunk_size
```
The parameter ```--heavy_chunk_size``` is used for the run_ted_segmentation process and should be set with maximum memory limits in mind.

## Running on HPC

## Install (with singularity)

These instructions are specific to the HPC setup in UCL Computer Sciences:

- Clone the GitHub repository
- Request access to the NextFlow submit node: `askey`
- Login to `askey`

Set the following NextFlow environment variables interactively or add to ~/.bashrc.

```bash
export NXF_OPTS='-Xms3g -Xmx3g'
export PATH=/share/apps/jdk-20.0.2/bin:$PATH
export LD_LIBRARY_PATH=/share/apps/jdk-20.0.2/lib:$LD_LIBRARY_PATH
export JAVA_HOME=/share/apps/jdk-20.0.2
export PATH=/share/apps/genomics/nextflow-local-23.04.2:$PATH
```

Create a cache directory for NextFlow (not entirely necessary but will prevent warnings).

```bash
mkdir ~/scratch
mkdir ~/scratch/nextflow_singularity_cache
export NXF_SINGULARITY_CACHEDIR=$HOME/Scratch/nextflow_singularity_cache
```

Set the following Python environment variables interactively or add to ~/.bashrc.

```bash
export PATH=/share/apps/python-3.13.0a6-shared/bin:$PATH
export LD_LIBRARY_PATH=/share/apps/python-3.13.0a6-shared/lib:$LD_LIBRARY_PATH
source /share/apps/source_files/python/python-3.13.0a6.source
```

Set up the venv environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

The latest containers are built and stored in GitHub Container Reposity (ghrc.io) as part of the automated build.

These can be downloaded as singularity images with `singularity pull`:

Note: the following requires setting up a [GitHub personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic)

```bash
singularity pull --docker-login domain-annotation-pipeline-script_latest.sif docker://ghcr.io/uclorengogroup/domain-annotation-pipeline-script:main-latest
singularity pull --docker-login domain-annotation-pipeline-cath-af-cli_latest.sif docker://ghcr.io/uclorengogroup/domain-annotation-pipeline-cath-af-cli:main-latest
singularity pull --docker-login domain-annotation-pipeline-ted-tools_latest.sif docker://ghcr.io/uclorengogroup/domain-annotation-pipeline-ted-tools:main-latest
```

The directory containing these singularity images can be added to your config file, or passed directly to nextflow:

```bash
nextflow run workflows/annotate -profile singularity \
    --singularity_image_dir "/path/to/singularity_images"
```
