process run_stride {
    label 'sge_low'
    container 'domain-annotation-pipeline-cath-af-cli'
    publishDir './results/stride', mode: 'copy'

    input:
    path '*'

    output:
    path '*.stride'

    script:
    """
    for f in *.pdb; do
        awk '!/^MODEL/ && !/^ENDMDL/' \$f > temp && mv temp \$f
        stride \$f > \${f%.pdb}.stride
    done
    """
}
