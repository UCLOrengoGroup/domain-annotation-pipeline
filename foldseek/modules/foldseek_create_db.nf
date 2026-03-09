process foldseek_create_db {
    label 'sge_low'
    container 'domain-annotation-pipeline-foldseek'
    
    input:
    tuple val(id), path(chopped_pdb_tar_file)

    output:
    tuple val(id), path("database_dir"), emit: query_db_dir

    script:
    """
    mkdir -p pdb database_dir
    tar -xzf ${chopped_pdb_tar_file} -C pdb
    ${params.foldseek_exec} createdb pdb database_dir/query_db
    rm -rf pdb
    """
    }