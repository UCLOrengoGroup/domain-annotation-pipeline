process chunk_ids_by_zip {
    label 'sge_low'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}" 
    publishDir "${params.results_dir}/intermediate", mode: 'copy', enabled: params.debug

    input:
    path   ids_file
    val    chunk_size

    output:
    path "chunk_mapping.tsv", emit: chunk_mapping

    script:
    """
    mkdir -p chunks

    chunk_by_zip.py \
        --input_file ${ids_file} \
        --chunk_size ${chunk_size} \
        --outdir \$PWD/chunks \
        --file_list chunk_mapping.tsv
    """
}

