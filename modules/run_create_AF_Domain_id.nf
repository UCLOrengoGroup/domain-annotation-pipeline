process run_AF_Domain_id {
    container 'domain-annotation-pipeline-cath-af-cli'
    stageInMode 'copy'
    publishDir 'results' , mode: 'copy'

    input:
    path transformed_file

    output:
    path "AF_Domain_ids.tsv"

    script:
    """
    awk '{ id = substr(\$1, 1, length(\$1) - 6); print id "/" \$4 }' ${transformed_file} > AF_Domain_ids.tsv
    """
}