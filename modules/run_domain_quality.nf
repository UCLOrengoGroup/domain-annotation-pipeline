process run_domain_quality {
    label 'sge_gpu_high'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-ted-tools:${params.container_tag_name}" 

    input:
    tuple val(id), path(chopped_pdb_tar_file)

    output:
    tuple val(id), path("domain_quality.csv")

    script:
    """
    mkdir -p pdb
    tar -xzf ${chopped_pdb_tar_file} -C pdb
    ${params.domain_quality_script_setup}
    ${params.domain_quality_script} -d pdb/ -o domain_quality.unsorted.csv
    perl -i.bak -pe 's/\\r\\n/\\n/g' domain_quality.unsorted.csv

    head -n 1 domain_quality.unsorted.csv > domain_quality.csv
    tail -n +2 domain_quality.unsorted.csv | sort -t, -k1,1 >> domain_quality.csv
    rm -rf pdb
    """
}
