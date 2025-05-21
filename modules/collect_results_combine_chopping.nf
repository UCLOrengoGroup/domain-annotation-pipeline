process collect_results {
    input:
    file 'chainsaw_results.tsv'
    file 'merizo_results.tsv'
    file 'unidoc_results.tsv'

    output:
    file 'domain_assignments.tsv'   // was all_results.tsv but seemed unnecessary to go through an intermediate file
    publishDir './results' , mode: 'copy'  

    script:
    """
    ${params.combine_script} \
        -m merizo_results.tsv \
        -u unidoc_results.tsv \
        -c chainsaw_results.tsv \
        -o domain_assignments.tsv
    """
}