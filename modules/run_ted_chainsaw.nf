process run_ted_chainsaw {
    label 'sge_gpu_high'
    container 'domain-annotation-pipeline-ted-tools'

    input:
    tuple(val(chunk_id), path(filtered_id_file), path(pdb_zip))

    output:
    tuple val(chunk_id), path('output/chopping_chainsaw_sorted.txt'), emit: chainsaw

    script:
    """
    # Lever 1: cap math-library threads to the cores reserved for this task so PyTorch/BLAS
    # don't oversubscribe shared CPU nodes (near no-op on GPU nodes, where inference is on the GPU).
    export OMP_NUM_THREADS=${task.cpus}
    export MKL_NUM_THREADS=${task.cpus}
    export OPENBLAS_NUM_THREADS=${task.cpus}

    #-- Extract from zip into filtered_pdbs (batches of 200 to improve efficiency) --
    mkdir -p filtered_pdbs
    awk 'NF {print \$0 ".pdb"}' ${filtered_id_file} > pdb_list.txt
    xargs -a pdb_list.txt -n 200 unzip -q ${pdb_zip} -d filtered_pdbs

    # ---------- Set up segmentation environment ----------
    ${params.run_segmentation_script_setup}
    mkdir -p output

    # ---------- Chainsaw (independent of Merizo/UniDoc) ----------
    bash scripts/segment.sh -i ./filtered_pdbs -m chainsaw -o ./output > output/chopping_chainsaw.log 2>&1
    if test ! -s output/chopping_chainsaw.txt; then
        echo "Chainsaw segmentation failed. Check log at output/chopping_chainsaw.log"
        exit 1
    fi

    sort output/chopping_chainsaw.txt > output/chopping_chainsaw_sorted.txt

    # ---------- Clean up filtered set ----------
    rm -rf filtered_pdbs
    """

    stub:
    """
    echo "Stub process for run_ted_chainsaw"
    mkdir -p output

    cp "${workflow.projectDir}/../assets/stub_run/chopping_chainsaw_sorted.txt" output/

    # Expand template so every synthetic ID in filtered_id_file gets the row
    # of its base/template ID, with column 1 replaced by the synthetic ID.
    awk -F '\\t' '
        BEGIN { OFS = FS }
        NR == FNR { template[\$1] = \$0; next }
        {
            synthetic_id = \$1
            base_id = synthetic_id
            sub(/-[0-9]+\$/, "", base_id)
            row = template[base_id]
            if (row == "") {
                print "ERROR: missing template row for " base_id > "/dev/stderr"
                exit 1
            }
            sub(/^[^\\t]+/, synthetic_id, row)
            print row
        }
    ' "output/chopping_chainsaw_sorted.txt" "${filtered_id_file}" > "output/chopping_chainsaw_sorted.txt.tmp"
    mv "output/chopping_chainsaw_sorted.txt.tmp" "output/chopping_chainsaw_sorted.txt"
    """
}
