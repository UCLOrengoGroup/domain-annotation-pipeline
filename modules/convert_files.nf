process convert_files {
    container 'domain-annotation-pipeline-script'
    publishDir './results', mode: 'copy'

    input:
    file 'chainsaw_results.tsv'
    file 'merizo_results.tsv'
    file 'unidoc_results.tsv'

    output:
    file 'merizo_results_reformatted.tsv'
    file 'unidoc_results_reformatted.tsv'

    script:
    """
    ${params.convert_script} -m merizo_results.tsv -c chainsaw_results.tsv -o merizo_results_reformatted.tsv
    ${params.convert_script} -u unidoc_results.tsv -c chainsaw_results.tsv -o unidoc_results_reformatted.tsv
    """
}
