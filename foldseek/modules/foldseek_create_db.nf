process foldseek_create_db {
    //tag "chunk_${task.index}"
    tag "chunk_${id}" // new
    publishDir "results", mode: 'copy'
    
    input:
    //path pdb_files
    tuple val(id), path(pdb_files) // new

    output:
    //path "database_dir_${task.index}", emit: query_db_dir
    tuple val(id), path("database_dir"), emit: query_db_dir // new

    script:
    //mkdir -p database_dir_${task.index}
    //    database_dir_${task.index}/query_db
    """
    mkdir -p input_pdbs
    cp ${pdb_files} input_pdbs/
    mkdir -p database_dir
    foldseek createdb \\
        input_pdbs \\
        database_dir/query_db
    """
    }