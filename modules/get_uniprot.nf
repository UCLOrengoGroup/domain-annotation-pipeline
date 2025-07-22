process get_uniprot_data {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'

    input:
    path uniprot_id_file

    output:
    path "uniprot_data.tsv"

    script:
    """
    ${params.fetch_uniprot_script} -a ${uniprot_id_file} -o uniprot_data.tsv
    """
}
