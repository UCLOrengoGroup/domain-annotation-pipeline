process prepare_pdb_file {
    label 'sge_low'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}" 
    publishDir "${params.results_dir}" , mode: 'copy', enabled: params.debug // only publish if run in debug mode

    input:
    path cif_zip

    output:
    path 'pdb_zip.zip'

    script:
    """
    cif_to_pdb.py "${cif_zip}" "pdb_zip.zip"
    """
}