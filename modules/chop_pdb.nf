process chop_pdb {
    container 'domain-annotation-pipeline-pdb-tools'
    stageInMode 'copy'
    publishDir './results/chopped_pdbs', mode: 'copy'   // Save PDB file to a directory for later use

    input:
    path consensus_file
    path '*'

    output:
    path '*.pdb'

    script:
    """
    ${params.chop_pdb_script} ${consensus_file}
    """
}