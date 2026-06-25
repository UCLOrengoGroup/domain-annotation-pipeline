process chunk_ids_by_zip {
    label 'sge_low'
    container "${params.singularity_image_dir}/domain-annotation-pipeline-script_latest.sif"
    publishDir "${params.results_dir}/intermediate", mode: 'copy', enabled: params.debug

    input:
    path   ids_file
    val    chunk_size
    path   script

    output:
    path "chunk_mapping.tsv", emit: chunk_mapping

    script:
    """
    mkdir -p chunks

    python3 ${script} \
        --input_file ${ids_file} \
        --chunk_size ${chunk_size} \
        --outdir \$PWD/chunks \
        --file_list chunk_mapping.tsv
    """
}

