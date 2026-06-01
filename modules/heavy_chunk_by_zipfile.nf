process heavy_chunk_by_zip {
    label 'sge_low'
    container "${params.singularity_image_dir}/domain-annotation-pipeline-script_latest.sif"
    publishDir "${params.results_dir}/intermediate", mode: 'copy' //, enabled: params.debug // only publish if run in debug mode
    
    input:
    path filtered_af_ids_file
    val heavy_chunk_size

    output:
    path "heavy_chunk_mapping.tsv", emit: chunk_mapping
    path "heavy_chunks", emit: chunk_dir


    script:
    """
    mkdir -p heavy_chunks

    python3 ${params.chunk_by_zip_script} \
    ${filtered_af_ids_file} \
    ${heavy_chunk_size} \
    \$PWD/heavy_chunks \
    heavy_chunk_mapping.tsv
    """
}