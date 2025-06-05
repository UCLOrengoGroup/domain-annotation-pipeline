process run_stride {
    container 'domain-annotation-pipeline-cath-af-cli'
    stageInMode 'copy'
    publishDir './results/stride', mode: 'copy'

    input:
    path '*'

    output:
    path '*.stride'

    script:
    """
    for f in *.pdb; do
        stride "\$f" > "\${f%.pdb}.stride"
    done
    """
}
