process light_chunk_consensus_by_zip {
    label 'sge_low'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}" 
    publishDir "${params.results_dir}/intermediate", mode: 'copy', enabled: params.debug // only publish if run in debug mode
    
    input:
    tuple val(parent_chunk_id), path(consensus_file), val(zip_name)
    val  light_chunk_size
    path script

    output:
    tuple val(parent_chunk_id), path("light_chunk_mapping.tsv"), emit: light_chunk_mapping


    script:
    """
    awk -v zip_name="${zip_name}" 'NF { print \$0 "\t" zip_name }' ${consensus_file} > consensus_with_zip.tsv

    mkdir -p light_chunks

    python3 ${script} \
        --consensus_file consensus_with_zip.tsv \
        --chunk_size ${light_chunk_size} \
        --outdir \$PWD/light_chunks \
        --file_list light_chunk_mapping.tsv
    """
}
