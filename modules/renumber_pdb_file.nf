process renumber_pdb_file {
    label 'sge_low'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}" 
    publishDir "${params.results_dir}", mode: 'copy', enabled: params.debug // only publish if run in debug mode
    publishDir "${params.results_dir}/resmaps", mode: 'copy', pattern: "resmaps_*.zip"

    input:
    tuple val(chunk_id), path(id_file), path(pdb_zip)

    output:
    tuple val(chunk_id),
        path(id_file),
        path("normalised_${chunk_id}.zip"),
        path("resmaps_${chunk_id}.zip"),
        emit: normalised
        tuple val(chunk_id), path("normalised_${chunk_id}.zip"), emit: normalised_zip
        tuple val(chunk_id), path("resmaps_${chunk_id}.zip"), emit: resmaps_zip

    script:
    """
    ${params.renumber_pdb_script} "${pdb_zip}" "${id_file}" "normalised_${chunk_id}.zip" "resmaps_${chunk_id}.zip"
    """
}