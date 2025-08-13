process run_plddt {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'
    publishDir "${params.results_dir}" , mode: 'copy'

    input:
    path pdb_dir

    output:
    path "domain_avg_plddt.tsv" 

    script:
    """
    ${params.plddt_script} ${pdb_dir} -o domain_avg_plddt.tsv
    """
}