#!/bin/bash
#$ -S /bin/bash
#$ -l h_rt=12:00:00          # Adjust time as needed
#$ -l tmem=32G               # Adjust memory if required
#$ -l gpu=true               # If pipeline needs GPU (Merizo does)
#$ -R y                      # Reuse node if possible
#$ -wd /home/nedmunds/domain-annotation-pipeline
#$ -j y                      # Join stdout and stderr
#$ -N domainAnnotate         # Job name

# Load environment modules and paths
export PATH=/share/apps/python-3.13.0a6-shared/bin:$PATH
export LD_LIBRARY_PATH=/share/apps/python-3.13.0a6-shared/lib:$LD_LIBRARY_PATH
source /share/apps/source_files/python/python-3.13.0a6.source

export PATH=/share/apps/jdk-20.0.2/bin:$PATH
export LD_LIBRARY_PATH=/share/apps/jdk-20.0.2/lib:$LD_LIBRARY_PATH
export JAVA_HOME=/share/apps/jdk-20.0.2

export PATH=/share/apps/genomics/nextflow-local-23.04.2:$PATH

# Configure JVM memory for Nextflow
export NXF_OPTS='-Xms5g -Xmx5g'

# Optional: Prevent container caching if needed
# export NXF_SINGULARITY_CACHEDIR=/home/${USER}/Scratch/nextflow_singularity_cache

# Dummy beforeScript path (if required in config)
mkdir -p ./platforms/ucl_cs_cluster
echo "#!/bin/bash" > ./platforms/ucl_cs_cluster/source
chmod +x ./platforms/ucl_cs_cluster/source

# Run the Nextflow pipeline
nextflow run workflows/annotate.nf \
  -c nextflow-with-singularity.config \
  --pdb_zip_file="/SAN/orengolab/bfvd/data/bfvd.zip" \
  -resume
