process convert_unidoc_results {
    label 'sge_low'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}" 

    input:
    file 'chainsaw_results.tsv'
    file 'unidoc_results.tsv'

    output:
    file 'unidoc_results_reformatted.tsv'

    script:
    """
    ${params.convert_script} -u unidoc_results.tsv -c chainsaw_results.tsv -o unidoc_results_reformatted.tsv
    """
}
