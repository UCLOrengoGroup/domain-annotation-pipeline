process foldseek_run_convertalis {

    publishDir "results/convertalis", mode: 'copy'
    
    input:
    path query_db
    path target_db
    path result_db_dir

    output:
    path "foldseek_output.m8", emit: m8_output
    path "versions.yml", emit: versions

    script:
    """
    foldseek convertalis \\
        ${query_db} \\
        ${target_db} \\
        foldseek_output_db \\
        foldseek_output.m8 \\
        --format-output "query,target,fident,evalue,qlen,tlen,qtmscore,ttmscore,qcov,tcov"

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        foldseek: \$(foldseek version | head -n1 | sed 's/foldseek //')
    END_VERSIONS
    """
}