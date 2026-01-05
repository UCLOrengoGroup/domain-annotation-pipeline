process foldseek_run_convertalis {
    //tag "chunk_${task.index}"
    tag "chunk_${id}"
    publishDir "results/convertalis", mode: 'copy'
    
    input:
    //tuple path(query_db_dir), path(result_db_dir)
    tuple val(id), path(query_db_dir), path(result_db_dir)
    each path(target_db)
    //path result_db_dir

    output:
    //path "foldseek_output_${task.index}.m8", emit: m8_output
    tuple val(id), path("foldseek_output.m8"), emit: m8_output

    script:
    //foldseek_output_${task.index}.m8 \\
    """
    foldseek convertalis \\
        ${query_db_dir}/query_db \\
        ${target_db}/cath_v4_4_0_s95_db \\
        ${result_db_dir}/foldseek_output_db \\
        foldseek_output.m8 \\
        --format-output "query,target,fident,evalue,qlen,tlen,qtmscore,ttmscore,qcov,tcov"
    
    """
}