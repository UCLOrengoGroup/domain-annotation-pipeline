process chunk_ids_by_zip {
    label 'sge_low'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}" 
    publishDir "${params.results_dir}/intermediate", mode: 'copy', enabled: params.debug

    input:
    path   ids_file
    val    chunk_size
    path   script
    val    adaptive_chunking

    output:
    path "chunk_mapping.tsv", emit: chunk_mapping

    script:
    def adaptive_option = adaptive_chunking ? '--adaptive' : ''
    """
    mkdir -p chunks

    python3 ${script} \
        --input_file ${ids_file} \
        --chunk_size ${chunk_size} ${adaptive_option} \
        --outdir \$PWD/chunks \
        --file_list chunk_mapping.tsv
    """
}

