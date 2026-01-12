process foldseek_run_foldseek {
    tag "chunk_${id}"
    publishDir "results", mode: 'copy'
    
    input:
    tuple val(id), path(query_db_dir)
    each path(target_db)

    output:
    tuple val(id), path(query_db_dir), path("result_db_dir"), emit: search_results

    script:
    """
    mkdir -p tmp_foldseek
    mkdir -p result_db_dir
    ${params.foldseek_exec} search \\
        ${query_db_dir}/query_db \\
        ${target_db}/cath_v4_4_0_s95_db \\
        result_db_dir/foldseek_output_db \\
        tmp_foldseek \\
        --cov-mode 5 \\
        --alignment-type 2 \\
        -e 0.476641 \\
        -s 10 \\
        -c 0.459063 \\
        -a
    
    rm -rf tmp_foldseek
    
    """
}