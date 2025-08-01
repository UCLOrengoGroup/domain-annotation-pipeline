process create_md5 {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'

    input:
    path pdb_files
    
    output:
    path "*.tsv"
        
    script:
    """
    for pdb_file in ${pdb_files}; do
        base_name=\$(basename "\${pdb_file}" .pdb)
        ${params.md5_script} \${pdb_file} md5_\${pdb_file}.tsv
    done
    """
}