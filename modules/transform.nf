process transform_consensus {
    label 'local_job'
    container 'domain-annotation-pipeline-script'
    publishDir 'results', mode: 'copy'

    input:
    path 'consensus_file'
    path 'all_md5_file'
    path 'stride_files/*.stride.summary'

    output:
    path "transformed_consensus.tsv"

    script:
    """
    ${params.transform_script} \
        -i 'consensus_file' \
        -o transformed_consensus.tsv \
        -m 'all_md5_file' \
        -s 'stride_files/' \
        --stride_summary_suffix .stride.summary
    """
}
