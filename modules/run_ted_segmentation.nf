process run_ted_segmentation {
    label 'sge_gpu_high'
    container 'domain-annotation-pipeline-ted-tools'

    input:
    tuple val(chunk_id), path(filtered_id_file)
    path(pdb_zip)

    output:    
    tuple val(chunk_id), path('output/chopping_chainsaw_sorted.txt'), emit: chainsaw
    tuple val(chunk_id), path('output/chopping_merizo_sorted.txt'), emit: merizo
    tuple val(chunk_id), path('output/chopping_unidoc_sorted.txt'), emit: unidoc
    tuple val(chunk_id), path('output/consensus_sorted.tsv'), emit: consensus
    tuple val(chunk_id), path('output/consensus.tsv.changed.txt'), emit: consensus_changed

    script:
    """
    #-- Extract from zip into filtered_pdbs (same logic as extract_pdb_from_zip but batches of 200 to improve efficiency) --
    mkdir -p filtered_pdbs
    awk 'NF {print \$0 ".pdb"}' ${filtered_id_file} > pdb_list.txt
    xargs -a pdb_list.txt -n 200 unzip -q ${pdb_zip} -d filtered_pdbs

    # ---------- Run segmentation on filtered set ----------
    ${params.run_segmentation_script_setup}
    
    which python3
    python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())"
    set -x
    uname -a
    pwd
    mkdir -p output
    ls -lrta
    ls -l /dev/nvidia* || true
    nvidia-smi -L || true
    env | sort
    ${params.run_segmentation_script} -i ./filtered_pdbs -o ./output
    
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
