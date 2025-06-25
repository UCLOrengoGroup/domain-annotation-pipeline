process collect_results_final {
    container 'domain-annotation-pipeline-script'
    stageInMode 'copy'
    publishDir './results', mode: 'copy'

    input:
    file 'transformed_consensus.tsv'
    file 'domain_globularity.tsv'
    file 'plddt_with_md5.tsv'
    file 'all_taxonomy.tsv'

    output:
    file 'final_results.tsv'

    script:
    """
    ${params.combine_final_script} \
        -t transformed_consensus.tsv \
        -g domain_globularity.tsv \
        -p plddt_with_md5.tsv \
        -x all_taxonomy.tsv \
        -o final_results.tsv
    """
}
