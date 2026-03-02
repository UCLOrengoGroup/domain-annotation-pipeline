// filter pdb files to only include those with > 25 residues. 10-Feb-26 added sort statement to for loop.
process filter_pdb_from_zip {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'

    input:
    tuple( val(chunk_id), path(id_file) )
    path pdb_zip
    val min_residues

    output:
    tuple( val(chunk_id), path('filtered_ids.txt'))

    script:
    """
    : > filtered_ids.txt

    # Call each chain name in the id_file (e.g. A0A001) chain_id
    while read -r chain_id; do
        [ -z "\$chain_id" ] && continue
        fname="\${chain_id}.pdb"
        
        # stream the data from the zip to pdb_wc file rather than unzipping 
        read model_count chain_count residue_count < <(
          unzip -p ${pdb_zip} "\$fname" 2>/dev/null | pdb_wc - 2>/dev/null | awk '
            /^No\\. models:/   {m=\$3}
            /^No\\. chains:/   {c=\$3}
            /^No\\. residues:/ {r=\$3}
            END {if (m=="" || c=="" || r=="") exit 1; print m, c, r} ') || { echo "WARNING: could not parse \$fname"; continue; }

        if [ "\$model_count" -ne 1 ]; then
            echo "WARNING: skipping \$fname, more than one model."
            continue
        fi

        if [ "\$chain_count" -ne 1 ]; then
            echo "WARNING: skipping \$fname, more than one chain."
            continue
        fi

        if [ "\$residue_count" -gt ${min_residues} ]; then
            echo "\$chain_id" >> filtered_ids.txt
        else
            echo "WARNING: Skipping \$fname, less than ${min_residues} residues."
        fi
    done < ${id_file}
    """
}
