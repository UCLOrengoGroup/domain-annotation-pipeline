process run_stride {
    label 'sge_low'
    container 'domain-annotation-pipeline-cath-af-cli'
    publishDir "${params.results_dir}" , mode: 'copy', enabled: params.debug // only publish if run in debug mode

    input:
    path '*'

    output:  //stride \$f > \${f%.pdb}.stride
    path '*.stride'

    script:
    """
    for f in *.pdb; do
        awk '!/^MODEL/ && !/^ENDMDL/' \$f > temp && mv temp \$f
        stride \$f > \${f%.pdb}.stride 2> \${f%.pdb}.stride.err || { 
        echo "STRIDE failed on \$f, see \${f%.pdb}.stride.err" 
        continue 
        }
    done
    """
}
