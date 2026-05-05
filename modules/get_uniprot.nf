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
    
    stub:
    """
    echo -e "accession\tproteome_id\ttax_common_name\ttax_scientific_name\ttax_lineage" > uniprot_data.tsv
    awk '{print \$1 "\tSTUB_PROTEOME\tStub common name\tStub scientific name\tcellular organisms; Stub lineage"}' ${uniprot_id_file} >> uniprot_data.tsv
    """
}
