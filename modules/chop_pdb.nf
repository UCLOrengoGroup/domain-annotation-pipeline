process chop_pdb {
    container 'domain-annotation-pipeline-pdb-tools'
    stageInMode 'copy'
    publishDir './results/chopped_pdbs', mode: 'copy'   // Save PDB file to a directory for later use

    input:
    path consensus_file
    path '*'

    output:
    path 'chopped_pdbs/*.pdb', emit: chop_files
    path 'chopped_pdbs', emit: chop_dir
    script:
    """
    mkdir chopped_pdbs
    ${params.chop_pdb_script} ${consensus_file} chopped_pdbs
    """
}