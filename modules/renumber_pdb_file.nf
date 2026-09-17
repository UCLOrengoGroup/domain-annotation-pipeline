process renumber_pdb_file {
    label 'sge_low'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}" 
    publishDir "${params.results_dir}", mode: 'copy', enabled: params.debug // only publish if run in debug mode
    publishDir "${params.results_dir}/resmaps", mode: 'copy', pattern: "resmaps_*.zip"
    publishDir "${params.results_dir}/errors", mode: 'copy', pattern: "renumber_pdb_errors_*.tsv" // publish Ids that failed

    input:
    tuple val(chunk_id), path(id_file), path(pdb_zip)
    path(renumber_script)

    output:
    tuple val(chunk_id),
        path(id_file),
        path("normalised_${chunk_id}.zip"),
        path("resmaps_${chunk_id}.zip"),
        emit: normalised
    tuple val(chunk_id), path("normalised_${chunk_id}.zip"), emit: normalised_zip
    tuple val(chunk_id), path("resmaps_${chunk_id}.zip"), emit: resmaps_zip
    tuple val(chunk_id), path("renumber_pdb_errors_${chunk_id}.tsv"), emit: errors

    script:
    """
    python3 ${renumber_script} \
        --input_zip "${pdb_zip}" \
        --id_file "${id_file}" \
        --normalised_zip "normalised_${chunk_id}.zip" \
        --resmaps_zip "resmaps_${chunk_id}.zip" \
        --error_file "renumber_pdb_errors_${chunk_id}.tsv"
    """
}