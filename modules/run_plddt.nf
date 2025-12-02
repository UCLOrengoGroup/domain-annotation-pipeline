process run_plddt {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'
    publishDir "${params.results_dir}" , mode: 'copy'

    input:
    tuple val(id), path("pdb/*")

    output:
    tuple val(id), path("domain_avg_plddt.tsv")

    script:
    """
    ${params.plddt_script} ./pdb -o domain_avg_plddt.tsv
    """
}