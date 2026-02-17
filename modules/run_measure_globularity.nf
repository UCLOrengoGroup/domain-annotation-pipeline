process run_measure_globularity {
    label 'sge_low'
    container 'domain-annotation-pipeline-cath-af-cli'
    publishDir "${params.results_dir}" , mode: 'copy'

    input:
    tuple val(id), path("pdb/*") //pdb_dir

    output:
    tuple val(id), path("domain_globularity.tsv") 

    // added an intermediate tmp file and dos2unix to recognise end of lines correctly.
    script:
    """
    ${params.globularity_script} --pdb_dir ./pdb --domain_globularity domain_globularity_tmp.tsv
    dos2unix -n domain_globularity_tmp.tsv domain_globularity.unsorted.tsv || tr -d '\\r' < domain_globularity_tmp.tsv > domain_globularity.unsorted.tsv
    head -n 1 domain_globularity.unsorted.tsv > domain_globularity.tsv
    tail -n +2 domain_globularity.unsorted.tsv | sort >> domain_globularity.tsv
    """
}