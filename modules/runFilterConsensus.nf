/*
 * Run filter_domains_consensus.py on the filtered consensus file consensus.tsv output from renGetConsensus.
 * Command format: python filter_domains_consensus.py consensus.tsv -o filtered_consensus_1.tsv.
 */
process runFilterConsensus {
    container 'domain-annotation-pipeline-ted-tools'
    stageInMode 'copy'
    publishDir './results' , mode: 'copy'

    input:
      path consensus_file

    output:
        path "filtered_consensus.tsv"
        path "*.changed.txt"

    script:
    """
    ${params.postfilter_script} ${consensus_file} -o filtered_consensus.tsv
    """
}