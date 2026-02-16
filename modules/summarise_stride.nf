process summarise_stride {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'
    publishDir "${params.results_dir}" , mode: 'copy', enabled: params.debug // only publish if run in debug mode

    input:
    tuple val(id), path(stride_files)

    output:
    tuple val(id), path("stride_batch_${id}.summary")
    
    script:
    """
    ${params.stride_summary_script} -o stride_batch_${id}.unsorted.summary -d . --suffix .stride
    
    head -n 1 stride_batch_${id}.unsorted.summary > stride_batch_${id}.summary
    tail -n +2 stride_batch_${id}.unsorted.summary | sort >> stride_batch_${id}.summary
    """
}
