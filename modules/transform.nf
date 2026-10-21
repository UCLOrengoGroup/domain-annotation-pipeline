process transform_consensus {
    label 'sge_low'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}"
    publishDir "${params.results_dir}" , mode: 'copy'

    input:
    path transform_script
    path 'consensus_file'
    path 'all_md5_file'
    path 'all_stride_file'

    output:
    path "transformed_consensus.tsv"

    script:
    """
    python3 ${transform_script} \
        -i 'consensus_file' \
        -o transformed_consensus.tsv \
        -m 'all_md5_file' \
        -s 'all_stride_file'
    """
}
