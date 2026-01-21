process foldseek_create_db {
    label 'sge_low'
    container 'domain-annotation-pipeline-foldseek'
    publishDir "results", mode: 'copy'
    
    input:
    tuple val(id), path(pdb_files)

    output:
    tuple val(id), path("database_dir"), emit: query_db_dir

    script:
    """
    mkdir -p database_dir
    ${params.foldseek_exec} createdb \\
        . \\
        database_dir/query_db
    """
    }