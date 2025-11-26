process run_measure_globularity {
    label 'sge_low'
    container 'domain-annotation-pipeline-cath-af-cli'
    publishDir "${params.results_dir}" , mode: 'copy'

    input:
    tuple val(id), path("pdb/*") //pdb_dir

    output:
    tuple val(id), path("domain_globularity.tsv")
    
    script:
    """
    ${params.globularity_script} --pdb_dir ./pdb --domain_globularity domain_globularity.tsv
    """
}