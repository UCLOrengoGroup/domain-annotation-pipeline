process get_uniprot_data {
    label 'local_job'
    container 'domain-annotation-pipeline-script'

    input:
    val uniprot_id

    output:
    path "uniprot_*.tsv"

    script:
    """
    ${params.fetch_uniprot_script} -a ${uniprot_id} -o uniprot_${uniprot_id}.tsv
    """
}
