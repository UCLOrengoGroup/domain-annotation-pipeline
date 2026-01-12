process foldseek_create_db {
    publishDir "results", mode: 'copy'
    
    input:
    tuple val(id), path(pdb_files)

    output:
    tuple val(id), path("database_dir"), emit: query_db_dir

    script:
    """
    mkdir -p input_pdbs
    cp ${pdb_files} input_pdbs/
    mkdir -p database_dir
    ${params.foldseek_exec} createdb \\
        input_pdbs \\
        database_dir/query_db
    """
    }