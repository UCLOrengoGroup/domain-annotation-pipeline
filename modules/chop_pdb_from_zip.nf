process chop_pdb_from_zip {
    label 'sge_low'
    container 'domain-annotation-pipeline-script' 
    publishDir "${params.results_dir}/chopped_pdbs" , mode: 'copy'

    input:
    tuple val(id), path(consensus_chunk)
    path pdb_zip

    output:
    tuple val(id), path("${id}_chopped_pdbs.tar.gz")
    
    script:
    """
    mkdir -p chopped_pdbs
    ${params.chop_pdb_script} --consensus ${consensus_chunk} --pdb-zip ${pdb_zip} --output chopped_pdbs
    tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf ${id}_chopped_pdbs.tar.gz -C chopped_pdbs .
    rm -rf chopped_pdbs
    """
}
