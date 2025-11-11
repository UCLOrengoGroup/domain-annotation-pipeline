process run_quality_checks {

    input:
    path "pdb/*.pdb"

    output:
    path "domain_quality.csv"

    script:
    """
    ${params.domain_quality_script} -d pdb/ -o domain_quality.csv
    """
}
