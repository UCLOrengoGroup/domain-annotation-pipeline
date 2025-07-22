#!/bin/bash
#$ -S /bin/bash
#$ -l h_rt=4:00:00
#$ -l tmem=31G
#$ -wd /home/nedmunds/domain-annotation-pipeline
#$ -j y
#$ -N domainAnnotate

# Load any necessary environment modules (if applicable)
export PATH=/share/apps/python-3.13.0a6-shared/bin:$PATH
export LD_LIBRARY_PATH=/share/apps/python-3.13.0a6-shared/lib:$LD_LIBRARY_PATH
source /share/apps/source_files/python/python-3.13.0a6.source
export NXF_OPTS='-Xms5g -Xmx5g' # Modify the heap size accordingly
export PATH=/share/apps/jdk-20.0.2/bin:$PATH
export LD_LIBRARY_PATH=/share/apps/jdk-20.0.2/lib:$LD_LIBRARY_PATH
export JAVA_HOME=/share/apps/jdk-20.0.2
export PATH=/share/apps/genomics/nextflow-local-23.04.2:$PATH

# Optional: Activate your conda or virtualenv if needed
# source activate myenv

# Run Nextflow
nextflow run workflows/annotate.nf -c nextflow-with-singularity.config -resume