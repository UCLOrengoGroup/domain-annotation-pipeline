process convert_merizo_results {
    label 'local'
    container 'domain-annotation-pipeline-script'

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
