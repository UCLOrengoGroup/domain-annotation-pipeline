process light_chunk_consensus_by_zip {
    label 'sge_low'
    container "${params.singularity_image_dir}/domain-annotation-pipeline-script_latest.sif"
    publishDir "${params.results_dir}/intermediate", mode: 'copy', enabled: params.debug // only publish if run in debug mode
    
    input:
    path consensus_file
    val  light_chunk_size
    path script

    output:
    path "light_chunk_mapping.tsv", emit: light_chunk_mapping


    script:
    """
    mkdir -p light_chunks

    python3 ${script} \
        --consensus_file ${consensus_file} \
        --chunk_size ${light_chunk_size} \
        --outdir \$PWD/light_chunks \
        --file_list light_chunk_mapping.tsv
    """
}
