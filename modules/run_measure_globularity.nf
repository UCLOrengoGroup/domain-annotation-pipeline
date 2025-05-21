process run_measure_globularity {
    container 'domain-annotation-pipeline-cath-af-cli'
    stageInMode 'copy'
    publishDir 'results' , mode: 'copy'

    input:
    path pdb_dir

    output:
    path "domain_globularity.tsv"
    //mkdir -p chopped_pdbs  then   cp ${pdb_files} chopped_pdbs/
    
    script:
    """
    ${params.globularity_script} --pdb_dir ${pdb_dir} --domain_globularity domain_globularity.tsv
    """
}