process collect_results_final {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'
    publishDir "${params.results_dir}" , mode: 'copy'

    input:
    path combine_script
    file 'transformed_consensus.tsv'
    file 'domain_globularity.tsv'
    file 'plddt_with_md5.tsv'
    file 'domain_quality.csv'
    file 'all_taxonomy.tsv'
    file 'foldseek_parsed_results.tsv'

    output:
    file 'final_results.tsv'

    script:
    """
    python3 ${combine_script} \
        -t transformed_consensus.tsv \
        -g domain_globularity.tsv \
        -p plddt_with_md5.tsv \
        -q domain_quality.csv \
        -x all_taxonomy.tsv \
        -f foldseek_parsed_results.tsv \
        -o final_results.tsv
    """
}
