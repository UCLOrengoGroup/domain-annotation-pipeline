process run_measure_globularity {
    label 'sge_low'
    container 'domain-annotation-pipeline-cath-af-cli'
    publishDir "${params.results_dir}" , mode: 'copy', enabled: params.debug

    input:
    tuple val(id), path(chopped_pdb_tar_file)

    output:
    tuple val(id), path("domain_globularity.tsv") 

    // added an intermediate tmp file and dos2unix to recognise end of lines correctly.
    script:
    """
    mkdir -p pdb
    tar -xzf ${chopped_pdb_tar_file} -C pdb
    ${params.globularity_script} --pdb_dir ./pdb --domain_globularity domain_globularity_tmp.tsv
    dos2unix -n domain_globularity_tmp.tsv domain_globularity.unsorted.tsv || tr -d '\\r' < domain_globularity_tmp.tsv > domain_globularity.unsorted.tsv
    head -n 1 domain_globularity.unsorted.tsv > domain_globularity.tsv
    tail -n +2 domain_globularity.unsorted.tsv | sort >> domain_globularity.tsv
    rm -rf pdb
    """
}