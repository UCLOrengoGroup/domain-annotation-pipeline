process summarise_stride {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'
    publishDir './results/stride', mode: 'copy'

    input:
    path '*.stride'

    output:
    path "stride.summary"

    script:
    """
    ${params.stride_summary_script} -o stride.summary -d . --suffix .stride
    """
}
