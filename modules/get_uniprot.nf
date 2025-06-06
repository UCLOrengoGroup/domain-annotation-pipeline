process get_uniprot_data {
    container 'domain-annotation-pipeline-script'
    stageInMode 'copy'

    input:
    val uniprot_id

    output:
    path "uniprot_*.tsv"

    script:
    """
    ${params.fetch_uniprot_script} ${uniprot_id} uniprot_${uniprot_id}.tsv
    """
}
