process run_merizo {
    label 'gpu_job'

    input:
    path '*'

    output:
    path 'merizo_results.csv'

    script:
    """
    ${params.merizo_script} -d cpu -i *.pdb > merizo_results.csv
    """
}
