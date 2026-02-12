process run_ted_segmentation {
    label 'sge_gpu_high'
    container 'domain-annotation-pipeline-ted-tools'

    input:
    tuple val(chunk_id), path('pdb/*')

    output:    
    tuple val(chunk_id), path('output/chopping_chainsaw_sorted.txt'), emit: chainsaw
    tuple val(chunk_id), path('output/chopping_merizo_sorted.txt'), emit: merizo
    tuple val(chunk_id), path('output/chopping_unidoc_sorted.txt'), emit: unidoc
    tuple val(chunk_id), path('output/consensus_sorted.tsv'), emit: consensus
    tuple val(chunk_id), path('output/chopping_chainsaw.log'), emit: chainsaw_log
    tuple val(chunk_id), path('output/chopping_merizo.log'), emit: merizo_log
    tuple val(chunk_id), path('output/chopping_unidoc.log'), emit: unidoc_log
    tuple val(chunk_id), path('output/consensus.log'), emit: consensus_log
    tuple val(chunk_id), path('output/consensus.tsv.changed.txt'), emit: consensus_changed

    script:
    """
    ${params.run_segmentation_script_setup}
    
    which python3
    python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())"
    set -x
    uname -a
    pwd
    mkdir output
    ls -lrta
    ls -l /dev/nvidia* || true
    nvidia-smi -L || true
    env | sort
    ${params.run_segmentation_script} -i ./pdb -o ./output
    
    sort output/chopping_chainsaw.txt > output/chopping_chainsaw_sorted.txt
    sort output/chopping_merizo.txt > output/chopping_merizo_sorted.txt
    sort output/chopping_unidoc.txt > output/chopping_unidoc_sorted.txt
    sort output/consensus.tsv > output/consensus_sorted.tsv
    """


    stub:
    """
    echo "Stub process for run_ted_segmentation"
    rsync -av /launchDir/fixtures/debug/run_ted_segmentation/ ./
    """
}
