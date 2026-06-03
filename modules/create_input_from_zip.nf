process create_input_from_zip {
    label 'sge_low'
    container "${params.singularity_image_dir}/domain-annotation-pipeline-script_latest.sif"
    publishDir "${params.results_dir}/intermediate", mode: 'copy' //, enabled: params.debug // only publish if run in debug mode
    
    input:
    path input_zip_dir

    output:
    path "input_mapping.tsv"

    script:
    """
    python3 ${params.create_input_from_zip_script} \
        --input_zip_dir ${input_zip_dir} \
        --output input_mapping.tsv
    """
}