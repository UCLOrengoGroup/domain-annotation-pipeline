process run_ted_segmentation {
    label 'sge_gpu_high'
    container 'domain-annotation-pipeline-ted-tools'

    input:
    path 'pdb/*'

    output:    
    path 'output/chopping_chainsaw.txt', emit: chainsaw
    path 'output/chopping_merizo.txt', emit: merizo
    path 'output/chopping_unidoc.txt', emit: unidoc
    path 'output/consensus.tsv', emit: consensus
    path 'output/chopping_chainsaw.log', emit: chainsaw_log
    path 'output/chopping_merizo.log', emit: merizo_log
    path 'output/chopping_unidoc.log', emit: unidoc_log
    path 'output/consensus.log', emit: consensus_log
    path 'output/consensus.tsv.changed.txt', emit: consensus_changed

    script:
    """
    TMP_LOCAL_WORKDIR=\$PWD
    echo "Running TED segmentation on PDB files in \$TMP_LOCAL_WORKDIR/pdb"
    ${params.run_segmentation_script} -i \$TMP_LOCAL_WORKDIR/pdb -o ./output
    cd \$TMP_LOCAL_WORKDIR
    """
}
