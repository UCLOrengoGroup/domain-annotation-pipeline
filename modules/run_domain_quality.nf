process run_domain_quality {
    label 'sge_gpu_high'
    container 'domain-annotation-pipeline-ted-tools'

    input:
    tuple val(id), path("chopped_pdbs/*")

    output:
    tuple val(id), path("domain_quality.csv")

    script:
    """
    ${params.domain_quality_script_setup}
    ${params.domain_quality_script} -d chopped_pdbs/ -o domain_quality.csv
    perl -i.bak -pe 's/\\r\\n/\\n/g' domain_quality.csv
    """
}
