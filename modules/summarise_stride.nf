process summarise_stride {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'
    publishDir './results/stride', mode: 'copy'

    input:
    path stride_files

    output:
    path "stride_batch_*.summary"

    script:
    """
    batch_id=\$(date +%s%N | cut -b1-13)
    ${params.stride_summary_script} -o stride_batch_\${batch_id}.summary -d . --suffix .stride
    """
}
