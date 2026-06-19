process create_input_from_zip {
    container 'domain-annotation-pipeline-script'
    publishDir "${params.results_dir}/intermediate", mode: 'copy' //, enabled: params.debug // only publish if run in debug mode
    
    input:
    path input_zip_dir
    path script

    output:
    path "input_mapping.tsv"

    script:
    """
    python3 ${script} \\
        --input_zip_dir ${input_zip_dir} \
        --output input_mapping.tsv
    """
}
