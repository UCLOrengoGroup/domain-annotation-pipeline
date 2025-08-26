process run_foldseek {
    publishDir "results", mode: 'copy'
    
    input:
    path query_db_dir
    path target_db

    output:
    path "result_db_dir", emit: result_db_dir
    path "versions.yml", emit: versions

    script:
    """
    mkdir -p tmp_foldseek
    mkdir -p result_db_dir
    foldseek search \\
        ${query_db_dir}/query_db \\
        ${target_db}/cath_ssg5_fs_db \\
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