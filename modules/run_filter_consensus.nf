/*
 * Run filter_domains_consensus.py on the filtered consensus file consensus.tsv output from renGetConsensus.
 * Command format: python filter_domains_consensus.py consensus.tsv -o filtered_consensus_1.tsv.
 */
process run_filter_consensus {
    label 'sge_low'
    container 'domain-annotation-pipeline-ted-tools'
    publishDir './results' , mode: 'copy'

    input:
      path consensus_file

    output:
        path "filtered_consensus.tsv", emit: filtered
        path "*.changed.txt", emit: changed

    script:
    """
    ${params.postfilter_script} ${consensus_file} -o filtered_consensus.tsv
    """
}