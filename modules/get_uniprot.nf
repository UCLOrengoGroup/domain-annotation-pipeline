process get_uniprot_data {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'

    input:
    tuple val(id), path(uniprot_id_file)

    output:
    tuple val(id), path("uniprot_data.tsv")

    script:
    """
    ${params.fetch_uniprot_script} -i ${uniprot_id_file} -o uniprot_data.tsv
    """
}
