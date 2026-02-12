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
    ${params.domain_quality_script} -d chopped_pdbs/ -o domain_quality.unsorted.csv
    perl -i.bak -pe 's/\\r\\n/\\n/g' domain_quality.unsorted.csv

    head -n 1 domain_quality.unsorted.csv > domain_quality.csv
    tail -n +2 domain_quality.unsorted.csv | sort -t, -k1,1 >> domain_quality.csv
    """
}
