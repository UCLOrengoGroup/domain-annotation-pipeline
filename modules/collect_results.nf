process collect_results {
    input:
    file 'chainsaw_results.tsv'
    file 'merizo_results.tsv'
    file 'unidoc_results.tsv'

    output:
    file 'all_results.tsv'

    script:
    """
    ${params.combine_script} \
        -m merizo_results.tsv \
        -u unidoc_results.tsv \
        -c chainsaw_results.tsv \
        -o all_results.tsv
    """
}