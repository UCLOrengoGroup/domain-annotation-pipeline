process run_chainsaw {
    container 'domain-annotation-pipeline-chainsaw'
    stageInMode 'copy'
    input:
    path '*'

    output:
    path 'chainsaw_results.csv'

    """
    ${params.chainsaw_script} --structure_directory . -o chainsaw_results.csv
    sed -i '/^chain_id/d' chainsaw_results.csv
    """
}