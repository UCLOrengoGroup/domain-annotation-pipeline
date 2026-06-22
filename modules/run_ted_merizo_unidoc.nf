process run_ted_merizo_unidoc {
    label 'sge_gpu_high'
    container 'domain-annotation-pipeline-ted-tools'

    input:
    tuple(val(chunk_id), path(filtered_id_file), path(pdb_zip))

    output:
    tuple val(chunk_id), path('output/chopping_merizo_sorted.txt'), emit: merizo
    tuple val(chunk_id), path('output/chopping_unidoc_sorted.txt'), emit: unidoc

    script:
    """
    #-- Extract from zip into filtered_pdbs (batches of 200 to improve efficiency) --
    mkdir -p filtered_pdbs
    awk 'NF {print \$0 ".pdb"}' ${filtered_id_file} > pdb_list.txt
    xargs -a pdb_list.txt -n 200 unzip -q ${pdb_zip} -d filtered_pdbs

    # ---------- Set up segmentation environment ----------
    ${params.run_segmentation_script_setup}
    mkdir -p output

    # ---------- Merizo (UniDoc inherits Merizo's chopping) ----------
    bash scripts/segment.sh -i ./filtered_pdbs -m merizo -o ./output > output/chopping_merizo.log 2>&1
    if test ! -s output/chopping_merizo.txt; then
        echo "Merizo segmentation failed. Check log at output/chopping_merizo.log"
        exit 1
    fi

    bash scripts/segment.sh -i ./filtered_pdbs -m unidoc -o ./output -c output/chopping_merizo.txt > output/chopping_unidoc.log 2>&1
    if test ! -s output/chopping_unidoc.txt; then
        echo "UniDoc segmentation failed. Check log at output/chopping_unidoc.log"
        exit 1
    fi

    sort output/chopping_merizo.txt > output/chopping_merizo_sorted.txt
    sort output/chopping_unidoc.txt > output/chopping_unidoc_sorted.txt

    # ---------- Clean up filtered set ----------
    rm -rf filtered_pdbs
    """

    stub:
    """
    echo "Stub process for run_ted_merizo_unidoc"
    mkdir -p output

    cp "${workflow.projectDir}/../assets/stub_run/chopping_merizo_sorted.txt" output/
    cp "${workflow.projectDir}/../assets/stub_run/chopping_unidoc_sorted.txt" output/

    # Expand each template file so every synthetic ID in filtered_id_file gets the row
    # of its base/template ID, with column 1 replaced by the synthetic ID.
    for f in chopping_merizo_sorted.txt chopping_unidoc_sorted.txt; do
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
        ' "output/\${f}" "${filtered_id_file}" > "output/\${f}.tmp"
        mv "output/\${f}.tmp" "output/\${f}"
    done
    """
}
