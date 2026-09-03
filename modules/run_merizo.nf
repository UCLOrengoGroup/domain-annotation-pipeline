process run_merizo {
    label 'sge_gpu_high'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-ted-tools:${params.container_tag_name}"

    input:
    path '*'

    output:
    path 'merizo_results.csv'

    script:
    """
    ${params.merizo_script} -i *.pdb --iterate > merizo_results.csv
    """
}
