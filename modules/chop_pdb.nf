process chop_pdb {
    label 'sge_low'
    container 'domain-annotation-pipeline-pdb-tools' 
    publishDir "${params.results_dir}" , mode: 'copy'

    input:
    path consensus_file
    path '*'

    output:
    path 'chopped_pdbs/*.pdb'  //, emit: chop_files
    //path 'chopped_pdbs', emit: chop_dir
    
    script:
    """
    mkdir chopped_pdbs 
    ${params.chop_pdb_script} ${consensus_file} chopped_pdbs
    """
}