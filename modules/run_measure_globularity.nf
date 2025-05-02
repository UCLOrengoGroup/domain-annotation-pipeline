process run_measure_globularity {
    container 'domain-annotation-pipeline-cath-af-cli'
    stageInMode 'copy'
    publishDir 'results' , mode: 'copy'

    input:
    path consensus_dom_file
    path '*.pdb'

    output:
    path "domain_globularity.tsv"

    script:
    """
    ${params.globularity_script} \
        --consensus_domain_list ${consensus_dom_file} \
        --pdb_dir results/chopped_pdbs \
        --domain_globularity domain_globularity.tsv \
    """
}