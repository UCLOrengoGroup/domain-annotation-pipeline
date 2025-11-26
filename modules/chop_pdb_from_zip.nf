process chop_pdb_from_zip {
    label 'sge_low'
    container 'domain-annotation-pipeline-script' 
    publishDir "${params.results_dir}/chopped_pdbs" , mode: 'copy'

    input:
    tuple val(id), path(consensus_chunk)
    path pdb_zip

    output:
    tuple val(id), path('chopped_pdbs/*.pdb')
    
    script:
    """
    mkdir -p chopped_pdbs
    ${params.chop_pdb_script} --consensus ${consensus_chunk} --pdb-zip ${pdb_zip} --output chopped_pdbs
    """
}
