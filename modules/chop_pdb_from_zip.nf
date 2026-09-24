process chop_pdb_from_zip {
    label 'sge_low'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}" 
    memory 8.GB
    publishDir "${params.results_dir}/chopped_pdbs" , mode: 'copy'

    input:
    tuple val(id), path(consensus_chunk), path(pdb_zip)

    output:
    tuple val(id), path("${id}_chopped_pdbs.tar.gz"), emit: chopped_pdbs, optional: true
    tuple val(id), path("${id}_empty_file_error.tar.gz"), emit: empty_error_pdbs, optional: true
    
    script:
    """
    mkdir -p chopped_pdbs
    ${params.chop_pdb_script} --consensus ${consensus_chunk} --pdb-zip ${pdb_zip} --output chopped_pdbs
    tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf ${id}_chopped_pdbs.tar.gz -C chopped_pdbs .
    
    if ! tar -tzf ${id}_chopped_pdbs.tar.gz | grep -q '\\.pdb'; then
        mv ${id}_chopped_pdbs.tar.gz ${id}_empty_file_error.tar.gz
    fi

    rm -rf chopped_pdbs
    """
}
