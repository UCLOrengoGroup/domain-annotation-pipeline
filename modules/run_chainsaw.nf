process run_chainsaw {
    label 'sge_job'
    container 'domain-annotation-pipeline-chainsaw'

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