process run_merizo {
    container 'domain-annotation-pipeline-merizo'
    stageInMode 'copy'

    input:
    path '*'

    output:
    path 'merizo_results.csv'

    """
    ${params.merizo_script} -d cpu -i *.pdb > merizo_results.csv
    """
}