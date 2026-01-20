process foldseek_run_convertalis {
    label 'sge_low'
    container 'domain-annotation-pipeline-foldseek'
    publishDir "results/convertalis", mode: 'copy'
    
    input:
    tuple val(id), path(query_db_dir), path(result_db_dir)
    path(target_db)

    output:
    tuple val(id), path("foldseek_output.m8"), emit: m8_output

    script:
    """
    ${params.foldseek_exec} convertalis \\
        ${query_db_dir}/query_db \\
        ${target_db}/${params.foldseek_db_name} \\
        ${result_db_dir}/foldseek_output_db \\
        foldseek_output.m8 \\
        --format-output "query,target,fident,evalue,qlen,tlen,qtmscore,ttmscore,qcov,tcov"
    
    """
}