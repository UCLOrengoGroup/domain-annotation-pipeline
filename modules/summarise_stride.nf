process summarise_stride {
    container 'domain-annotation-pipeline-script'
    stageInMode 'copy'
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
