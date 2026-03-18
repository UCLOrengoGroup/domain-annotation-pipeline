process get_uniprot_data {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'

    input:
    tuple val(id), path(uniprot_id_file)

    output:
    tuple val(id), path("uniprot_data.tsv")

    script:
    """
    # If IDs look like MGnify ids (length > 10), skip the UniProt fetch as they won't exist and get_uniprot will fail.
    first_id=\$(head -n 1 ${uniprot_id_file})

    if [ \${#first_id} -gt 10 ]; then         
        # Create a dummy file with the correct column headers
        printf "accession\tproteome_id\ttax_common_name\ttax_scientific_name\ttax_lineage\n" > uniprot_data.tsv
        # Then add blank taxonomy rows for all IDs
        awk '{print \$1 "\t\t\t\t"}' ${uniprot_id_file} >> uniprot_data.tsv
    else
    # fetch the ids from Uniprot as usual
    ${params.fetch_uniprot_script} -i ${uniprot_id_file} -o uniprot_data.tsv
    fi
    """
}
