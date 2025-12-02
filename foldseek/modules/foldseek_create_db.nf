process foldseek_create_db {
    tag "chunk_${task.index}"
    publishDir "results", mode: 'copy'
    
    input:
    path pdb_files

    output:
    path "database_dir_${task.index}", emit: query_db_dir

    script:
    """
    mkdir -p input_pdbs
    cp ${pdb_files} input_pdbs/
    mkdir -p database_dir_${task.index}
    foldseek createdb \\
        input_pdbs \\
        database_dir_${task.index}/query_db
    """
    }