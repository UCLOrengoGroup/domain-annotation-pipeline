process run_domain_quality_from_zip {
    label 'sge_gpu_high'
    container 'domain-annotation-pipeline-ted-tools'

    input:
    tuple val(id), path(pdb_list)
    path(pdb_zip)

    output:
    tuple val(id), path("domain_quality.csv")

    script:
    """
    ${params.domain_quality_script_setup}
    ${params.domain_quality_script} -z ${pdb_zip} --zip-list ${pdb_list} -o domain_quality.csv
    perl -i.bak -pe 's/\\r\\n/\\n/g' domain_quality.csv
    """
}
