process create_md5 {
    label 'sge_low'
    container 'domain-annotation-pipeline-cath-af-cli'

    input:
    path pdb_files
    file 'scripts/generate_md5.py' //added a new path.
    
    output:
    path "*.tsv"
    
    script:
    """
    for pdb_file in ${pdb_files}; do
        python3 scripts/generate_md5.py "\${pdb_file}"
    done
    """
}