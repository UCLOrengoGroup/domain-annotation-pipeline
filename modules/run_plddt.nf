process run_plddt {
    container 'domain-annotation-pipeline-cath-af-cli'
    stageInMode 'copy'
    publishDir 'results' , mode: 'copy'

    input:
    path cif_files
    path af_ids

    output:
    path "domain_plddt_and_lur.tsv"

    script:
    """
    mkdir -p cifs
    cp ${cif_files} cifs/
    ${params.plddt_script} --cif_in_dir cifs --id_file ${af_ids} --plddt_stats_file domain_plddt_and_lur.tsv
    """
}