process get_uniprot_data {
    label 'sge_low'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}" 

    input:
    tuple(val(id), path(id_file))

    output:
    tuple val(id), path("uniprot_data.tsv")

    script:
    """
    ${params.fetch_uniprot_script} -i ${id_file} -o uniprot_data.tsv
    """
    
    stub:
    """
    echo -e "accession\tproteome_id\ttax_common_name\ttax_scientific_name\ttax_lineage" > uniprot_data.tsv
    awk '{print \$1 "\tSTUB_PROTEOME\tStub common name\tStub scientific name\tcellular organisms; Stub lineage"}' ${id_file} >> uniprot_data.tsv
    """
}
