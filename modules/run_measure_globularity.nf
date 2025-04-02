process run_measure_globularity {
    input:
    path 'af_domain_list.csv'
    path '*.cif'

    output:
    path 'af_domain_globularity.csv'

    script:
    """
    cath-af-cli measure-globularity \
        --af_domain_list af_domain_list.csv \
        --af_chain_mmcif_dir . \
        --af_domain_globularity af_domain_globularity.csv \
    """
}