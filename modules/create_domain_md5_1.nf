process create_md5 {
    container 'domain-annotation-pipeline-script'
    stageInMode 'copy'
    publishDir 'results', mode: 'copy'

    input:
    path pdb_files // multiple files

    output:
    path "md5.tsv"

    script:
    """
    > md5.tsv
    for pdb in ${pdb_files.join(' ')}
    do
        ${params.md5_script} \$pdb >> md5.tsv
    done
    """
}
