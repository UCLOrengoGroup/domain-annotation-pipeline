process collect_results {
    label 'sge_low'
    publishDir "${params.results_dir}" , mode: 'copy'

    input:
    file 'domain_assignments.chainsaw.tsv' //updated file names
    file 'domain_assignments.merizo.tsv'
    file 'domain_assignments.unidoc.tsv'

    output:
    file 'domain_assignments.tsv'

    script:
    """
    combine_results.py \
        -m domain_assignments.merizo.tsv \
        -u domain_assignments.unidoc.tsv \
        -c domain_assignments.chainsaw.tsv \
        -o domain_assignments.tsv
    """
}
