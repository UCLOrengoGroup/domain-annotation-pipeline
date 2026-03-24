process run_plddt {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'
    publishDir "${params.results_dir}" , mode: 'copy', enabled: params.debug

    input:
    tuple val(id), path(chopped_pdb_tar_file)

    output:
    tuple val(id), path("domain_avg_plddt.tsv")

    script:
    """
    mkdir -p pdb
    tar -xzf ${chopped_pdb_tar_file} -C pdb
    ${params.plddt_script} ./pdb -o domain_avg_plddt.unsorted.tsv
    sort domain_avg_plddt.unsorted.tsv > domain_avg_plddt.tsv
    rm -rf pdb
    """
}