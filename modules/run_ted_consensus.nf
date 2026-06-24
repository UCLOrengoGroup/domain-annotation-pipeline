process run_ted_consensus {
    label 'sge_low'
    container 'domain-annotation-pipeline-ted-tools'

    input:
    tuple(val(chunk_id), path(merizo), path(unidoc), path(chainsaw), val(zip_name))

    output:
    tuple val(chunk_id), path('output/consensus_sorted.tsv'), val(zip_name), emit: consensus
    tuple val(chunk_id), path('output/consensus.tsv.changed.txt'), emit: consensus_changed

    script:
    """
    . /app/ted-tools/ted_consensus_1.0/ted_consensus/bin/activate
    mkdir -p output

    # Calculate consensus from Merizo, Chainsaw and UniDoc choppings
    ${params.getconsensus_script} -c ${merizo} ${chainsaw} ${unidoc} -o output/consensus.tsv > output/consensus.log 2>&1
    if test ! -f output/consensus.tsv; then
        echo "Consensus calculation failed. Check log at output/consensus.log"
        exit 1
    fi

    # Filter consensus domains (also writes output/consensus.tsv.changed.txt)
    ${params.postfilter_script} output/consensus.tsv -o output/consensus.tsv.tmp
    mv output/consensus.tsv.tmp output/consensus.tsv

    sort output/consensus.tsv > output/consensus_sorted.tsv
    """

    stub:
    """
    echo "Stub process for run_ted_consensus"
    mkdir -p output

    cp "${workflow.projectDir}/../assets/stub_run/consensus_sorted.tsv" output/

    # Expand the consensus template using the synthetic IDs present in the Merizo chopping.
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
    ' "output/consensus_sorted.tsv" "${merizo}" > "output/consensus_sorted.tsv.tmp"
    mv "output/consensus_sorted.tsv.tmp" "output/consensus_sorted.tsv"

    touch output/consensus.tsv.changed.txt
    """
}
