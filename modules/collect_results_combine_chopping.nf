process collect_results {
    label 'sge_low'
    publishDir './results', mode: 'copy'

    input:
    file 'chainsaw_results.tsv'
    file 'merizo_results.tsv'
    file 'unidoc_results.tsv'

    output:
    file 'domain_assignments.tsv'

    script:
    """
    ${params.combine_script} \
        -m merizo_results.tsv \
        -u unidoc_results.tsv \
        -c chainsaw_results.tsv \
        -o domain_assignments.tsv
    """
}
