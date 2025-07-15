process run_chainsaw {
    label 'gpu_job'

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
