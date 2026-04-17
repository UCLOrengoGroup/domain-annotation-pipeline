process prepare_pdb_file {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'
    publishDir "${params.results_dir}" , mode: 'copy', enabled: params.debug // only publish if run in debug mode

    input:
    path cif_zip

    output:
    path 'pdb_zip.zip'

    script:
    """
    ${params.cif_convert_script} "${cif_zip}" "pdb_zip.zip"
    """
}