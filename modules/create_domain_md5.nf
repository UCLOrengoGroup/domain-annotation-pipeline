process create_md5 {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'

    input:
    path pdb_file
    
    output:
    path "*.tsv"
        
    script:
    """
    ${params.md5_script} ${pdb_file} md5_${pdb_file}.tsv
    """
}