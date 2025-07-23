process convert_unidoc_results {
    label 'local'
    container 'domain-annotation-pipeline-script'

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
