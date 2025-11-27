process run_merizo {
    label 'sge_gpu_high'
    container 'domain-annotation-pipeline-merizo'

    input:
    path '*'

    output:
    path 'merizo_results.csv'

    script:
    """
    ${params.merizo_script} -i *.pdb --iterate > merizo_results.csv
    """
}
