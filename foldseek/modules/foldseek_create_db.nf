process foldseek_create_db {
    publishDir "results", mode: 'copy'
    
    input:
    path pdb_files

    output:
    path "database_dir/query_db", emit: query_db
    path "versions.yml", emit: versions

    script:
    """
    mkdir -p database_dir
    foldseek createdb \\
        ${pdb_files} \\
        database_dir/query_db

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        foldseek: \$(foldseek version | head -n1 | sed 's/foldseek //')
    END_VERSIONS
    """
    }