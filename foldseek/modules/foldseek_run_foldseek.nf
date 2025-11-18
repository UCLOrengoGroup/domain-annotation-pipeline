process foldseek_run_foldseek {
    publishDir "results", mode: 'copy'
    
    input:
    path query_db
    path target_db

    output:
    path "result_db_dir/foldseek_output_db", emit: result_db
    path "versions.yml", emit: versions

    script:
    """
    mkdir -p tmp_foldseek
    mkdir -p result_db_dir
    foldseek search \\
        ${query_db} \\
        ${target_db} \\
        result_db_dir/foldseek_output_db \\
        tmp_foldseek \\
        --cov-mode 5 \\
        --alignment-type 2 \\
        -e 0.108662 \\
        -s 10 \\
        -c 0.366757 \\
        -a
    
    rm -rf tmp_foldseek
    
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        foldseek: \$(foldseek version | head -n1 | sed 's/foldseek //')
    END_VERSIONS
    """
}