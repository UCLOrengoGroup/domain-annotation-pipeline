process run_plddt {
    label 'local_job'
    container 'domain-annotation-pipeline-script'
    publishDir 'results' , mode: 'copy'

    input:
    path pdb_dir

    output:
    path "domain_avg_plddt.tsv" 

    script:
    """
    ${params.plddt_script} ${pdb_dir} -o domain_avg_plddt.tsv
    """
}