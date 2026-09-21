// Retain single-model, single-chain PDBs with min_residues < length < max_residues.
process filter_pdb_from_zip {
    label 'sge_low'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}"

    input:
    tuple(val(chunk_id), path(id_file), path(pdb_zip))
    val min_residues
    val max_residues

    output:
    tuple(val(chunk_id), path('filtered_ids.txt'), val(pdb_zip.name))

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

        if [ "\$residue_count" -le ${min_residues} ]; then
            echo "WARNING: Skipping \$fname, not more than ${min_residues} residues."
        elif [ "\$residue_count" -ge ${max_residues} ]; then
            echo "WARNING: Skipping \$fname, at least ${max_residues} residues."
        else
            echo "\$chain_id" >> filtered_ids.txt
        fi

    done < ${id_file}
    """
}
