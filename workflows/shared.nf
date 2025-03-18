
process run_filter_domains_tsv {
    input:
    path 'domain_chopping_results.tsv'

    output:
    path 'domain_chopping_results.filtered.tsv'

    """
    ${params.ted_filter_domains_script} domain_chopping_results.tsv -o domain_chopping_results.filtered.tsv
    """
}