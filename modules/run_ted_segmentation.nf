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
    
    # ---------- Clean up filtered set ----------
    rm -rf filtered_pdbs
    """

    stub:
    """
    echo "Stub process for run_ted_segmentation"
    mkdir -p output

    # Copy the 5 template output files from the repo fixture folder
    cp "${workflow.projectDir}/../assets/stub_run/chopping_chainsaw_sorted.txt" output/
    cp "${workflow.projectDir}/../assets/stub_run/chopping_merizo_sorted.txt" output/
    cp "${workflow.projectDir}/../assets/stub_run/chopping_unidoc_sorted.txt" output/
    cp "${workflow.projectDir}/../assets/stub_run/consensus_sorted.tsv" output/
    cp "${workflow.projectDir}/../assets/stub_run/consensus.tsv.changed.txt" output/

    # Expand each template file so that every synthetic ID in filtered_id_file
    # gets the row of its base/template ID, but with column 1 replaced by the synthetic ID
    for f in chopping_chainsaw_sorted.txt chopping_merizo_sorted.txt chopping_unidoc_sorted.txt consensus_sorted.tsv; do
        awk -F '\\t' '
            BEGIN { OFS = FS }

            # Read template rows into a lookup keyed by base ID
            NR == FNR {
                template[\$1] = \$0
                next
            }

            # For each synthetic ID in the chunk input file
            {
                synthetic_id = \$1
                base_id = synthetic_id

                # Remove synthetic suffix like -0, -1, ... -9
                sub(/-[0-9]+\$/, "", base_id)

                row = template[base_id]

                if (row == "") {
                    print "ERROR: missing template row for " base_id > "/dev/stderr"
                    exit 1
                }

                # Replace first field with the synthetic ID
                sub(/^[^\\t]+/, synthetic_id, row)
                print row
            }
        ' "output/\${f}" "${filtered_id_file}" > "output/\${f}.tmp"

        mv "output/\${f}.tmp" "output/\${f}"
    done
    """
}
