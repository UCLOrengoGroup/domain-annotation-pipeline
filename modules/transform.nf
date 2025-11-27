process transform_consensus {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'
    publishDir "${params.results_dir}" , mode: 'copy'

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
