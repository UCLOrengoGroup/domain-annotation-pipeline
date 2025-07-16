process filter_pdb {
    // filter the pdb files
    // - only keep the first chain of the pdb file
    // - only keep pdb files with at least min_residues residues in the first chain

    label 'local_job'
    container 'domain-annotation-pipeline-pdb-tools'

    input:
    path pdb_ch
    val min_residues

    output:
    path 'filtered_pdbs/*.pdb'

    script:
    """
    mkdir -p chain_pdbs filtered_pdbs

    for pdb in ${pdb_ch}/*.pdb; do

        rm -f pdb_info.txt

        # use pdb_wc to get the number of chains and residues
        pdb_wc -c \$pdb > pdb_info.txt
        chain_count=\$(grep "No. chains:" pdb_info.txt | awk '{print \$3}')

        # TODO: provide option of how to handle multiple chains (rather than just erroring)
        if [ \$chain_count -ne 1 ]; then
            echo "ERROR: \$pdb: MULTIPLE_CHAINS (\$chain_count)"
            continue
        fi

        # get the first chain id
        first_chain_id=\$(tail -n 2 pdb_info.txt | head -n 1 | awk '{print \$2}' | tr ',' ' ' | awk '{print \$1}' )
        if [ -z "\$first_chain_id" ]; then
            echo "ERROR: \$pdb: NO_FIRST_CHAIN_ID"
            continue
        fi

        first_chain_pdb_file="chain_pdbs/\$(basename \$pdb)"

        echo "Processing \$pdb with first chain ID: \$first_chain_id"
        pdb_selchain -\$first_chain_id \$pdb > \$first_chain_pdb_file

        res_count=\$(pdb_wc -r \$first_chain_pdb_file | grep "No. residues:" | awk '{print \$3}')
        echo "Residue count in first chain: \$res_count"

        if [ \$res_count -lt ${min_residues} ]; then
            echo "ERROR: \$pdb: MIN_LENGTH (\$res_count < ${min_residues})"
            echo "\$pdb \$res_count" >> min_length_error.txt
            continue
        fi

        filtered_pdb_file="filtered_pdbs/\$(basename \$pdb)"

        echo "Keeping first chain pdb file: \$filtered_pdb_file"
        mv \$first_chain_pdb_file \$filtered_pdb_file

    done
    """
}
