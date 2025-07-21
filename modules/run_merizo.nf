process run_merizo {
    container 'domain-annotation-pipeline-merizo'

    input:
    path '*'

    output:
    path 'merizo_results.csv'

    script:
    """
    ${params.merizo_script} -d cpu -i *.pdb > merizo_results.csv
    """
}