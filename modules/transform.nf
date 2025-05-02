process transform_consensus {
    container 'domain-annotation-pipeline-script'
    stageInMode 'copy'
    publishDir 'results', mode: 'copy'   // Save PDB file to a directory for later use

    input:
    path 'consensus_file'
    path stride_summaries

    output:
    path "transformed_consensus.tsv"
        
    script:
    """
    ${params.transform_script} ${consensus_file} transformed_consensus.tsv ${stride_summaries}
    """
}