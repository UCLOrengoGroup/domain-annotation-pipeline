process transform_consensus {
    container 'domain-annotation-pipeline-script'
    stageInMode 'copy'
    publishDir 'results', mode: 'copy'

    input:
    path 'consensus_file'
    path all_md5_file
    path summaries_files

    output:
    path "transformed_consensus.tsv"
    
    script:
    """
    ${params.transform_script} -i ${consensus_file} -o transformed_consensus.tsv -m ${all_md5_file} -s ${summaries_files}
    """
}
