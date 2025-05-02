process run_stride {
    container 'domain-annotation-pipeline-cath-af-cli'
    stageInMode 'copy'

    input:
    path '*'

    output:
    path '*.stride'
    publishDir './results/stride' , mode: 'copy'
    
    script:
    """
    for f in *.pdb; do
        stride "\$f" > "\${f%.pdb}.stride"
    done
    """
}