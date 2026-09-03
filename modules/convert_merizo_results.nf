process convert_merizo_results {
    label 'sge_low'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}" 

    input:
    file 'chainsaw_results.tsv'
    file 'merizo_results.tsv'

    output:
    file 'merizo_results_reformatted.tsv'

    script:
    """
    ${params.convert_script} -m merizo_results.tsv -c chainsaw_results.tsv -o merizo_results_reformatted.tsv
    """
}
