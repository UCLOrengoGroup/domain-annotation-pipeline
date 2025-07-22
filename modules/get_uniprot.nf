process get_uniprot_data {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'

    input:
    path uniprot_id_file

    output:
    path "uniprot_*.tsv"

    script:
    """
    base=\$(basename ${uniprot_id_file} .txt)
    ${params.fetch_uniprot_script} -a ${uniprot_id_file} -o uniprot_\${base}.tsv
    """
}
