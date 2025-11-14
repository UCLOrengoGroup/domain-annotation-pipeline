process create_md5 {
    label 'sge_low'
    container 'domain-annotation-pipeline-cath-af-cli'

    input:
    path "pdb/*"
    
    output:
    path "output.tsv"
    
    script:
    """
    cath-af-cli pdb-to-md5 -d ./pdb -o output.tsv
    """
}