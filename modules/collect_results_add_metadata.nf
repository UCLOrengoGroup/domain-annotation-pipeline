process collect_results_final {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'
    publishDir "${params.results_dir}" , mode: 'copy'

    input:
    file 'transformed_consensus.tsv'
    file 'domain_globularity.tsv'
    file 'plddt_with_md5.tsv'
    file 'all_taxonomy.tsv'
    file 'foldseek_parsed_results.tsv'

    output:
    file 'final_results.tsv'

    script:
    """
    ${params.combine_final_script} \
        -t transformed_consensus.tsv \
        -g domain_globularity.tsv \
        -p plddt_with_md5.tsv \
        -x all_taxonomy.tsv \
        -f foldseek_parsed_results.tsv \
        -o final_results.tsv
    """
}
