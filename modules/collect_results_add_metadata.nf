process collect_results_final {
    label 'sge_low'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}" 
    publishDir "${params.results_dir}" , mode: 'copy'

    input:
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
    combine_results_final.py \
        -t transformed_consensus.tsv \
        -g domain_globularity.tsv \
        -p plddt_with_md5.tsv \
        -q domain_quality.csv \
        -x all_taxonomy.tsv \
        -f foldseek_parsed_results.tsv \
        -o final_results.tsv
    """
}
