process summarise_stride {
    container 'domain-annotation-pipeline-cath-af-cli'
    stageInMode 'copy'
    publishDir './results/stride' , mode: 'copy'
    
    input:
    path stride_file

    output:
    path "*.summary" //"summary_${stride_file.name}"

    script:
    """
    bash /app/get_stride_SSE.sh ${stride_file}
    """
}
