process run_chainsaw {
    label 'sge_gpu_high'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-ted-tools:${params.container_tag_name}" 

    input:
    path '*'

    output:
    path 'chainsaw_results.csv'

    script:
    """
    ${params.chainsaw_script} --structure_directory . -o chainsaw_results.csv
    sed -i '/^chain_id/d' chainsaw_results.csv
    """
}
