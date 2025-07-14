process run_measure_globularity {
    container 'domain-annotation-pipeline-cath-af-cli'
    publishDir 'results' , mode: 'copy'

    input:
    path pdb_dir

    output:
    path "domain_globularity.tsv"
    
    script:
    """
    ${params.globularity_script} --pdb_dir ${pdb_dir} --domain_globularity domain_globularity.tsv
    """
}