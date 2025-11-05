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
    ${params.run_segmentation_script_setup}
    which python3
    python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())"
    ${params.run_segmentation_script} -i ./pdb -o ./output
    """
}
