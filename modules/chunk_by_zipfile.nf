process chunk_by_zip {
    label 'sge_low'
    container "${params.singularity_image_dir}/domain-annotation-pipeline-script_latest.sif"
    publishDir "${params.results_dir}/intermediate", mode: 'copy' //, enabled: params.debug // only publish if run in debug mode
    
    input:
    path all_af_ids_file
    val chunk_size

    output:
    path "chunk_mapping.tsv", emit: chunk_mapping
    path "chunks", emit: chunk_dir


    script:
    """
    mkdir -p chunks

    python3 ${params.chunk_by_zip_script} \
    ${all_af_ids_file} \
    ${chunk_size} \
    \$PWD/chunks \
    chunk_mapping.tsv
    """
}