process create_md5 {
    container 'domain-annotation-pipeline-script'
    stageInMode 'copy'
    //publishDir 'results/md5', mode: 'copy'

    input:
    path pdb_file
    
    output:
    path "*.tsv"
        
    script:
    """
    ${params.md5_script} ${pdb_file} md5_${pdb_file}.tsv
    """
}