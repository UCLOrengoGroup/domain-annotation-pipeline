process run_measure_globularity {
    container 'domain-annotation-pipeline-cath-af-cli'
    stageInMode 'copy'
    publishDir 'results' , mode: 'copy'

    input:
    path pdb_files

    output:
    path "domain_globularity.tsv"

    script:
    """
    mkdir -p chopped_pdbs
    cp ${pdb_files} chopped_pdbs/
    ${params.globularity_script} --pdb_dir chopped_pdbs --domain_globularity domain_globularity.tsv
    """
}