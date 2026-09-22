// Validate PDBs and retain single-model, single-chain proteins within the length limits.
process filter_pdb_from_zip {
    label 'sge_low'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}"

    input:
    tuple(val(chunk_id), path(id_file), path(pdb_zip))
    val min_residues
    val max_residues
    path filter_script

    output:
    tuple(val(chunk_id), path('filtered_ids.txt'), val(pdb_zip.name)), emit: filtered_ids
    tuple(val(chunk_id), path('filter_metadata.tsv'), val(pdb_zip.name)), emit: metadata

    script:
    """
    python3 ${filter_script} \
        --pdb-zip ${pdb_zip} \
        --ids ${id_file} \
        --min-residues ${min_residues} \
        --max-residues ${max_residues} \
        --output-ids filtered_ids.txt \
        --output-metadata filter_metadata.tsv
    """
}
