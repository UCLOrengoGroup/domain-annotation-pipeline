process restore_pdb_numbering {
    label 'sge_low'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}" 
    publishDir "${params.results_dir}/restored_chopped_pdbs", mode: 'copy'

    input:
    tuple val(chunk_id), path(chopped_pdb_file), path(resmap_zip)
    path restore_script

    output:
    path("${chunk_id}_chopped_pdbs.tar.gz")

    script:
    """
    mkdir -p restored_chopped_pdbs resmaps

    tar -xzf ${chopped_pdb_file} -C restored_chopped_pdbs
    unzip -q ${resmap_zip} -d resmaps

    python3 ${restore_script} restored_chopped_pdbs resmaps

    tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf ${chunk_id}_chopped_pdbs.tar.gz -C restored_chopped_pdbs .
    rm -rf restored_chopped_pdbs resmaps
    """
}