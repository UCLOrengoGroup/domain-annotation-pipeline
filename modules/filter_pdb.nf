// filter pdb files to only include those with > 25 residues 
process filter_pdb {
    label 'sge_low'
    container 'domain-annotation-pipeline-script'

    input:
    tuple( val(id), path("*") )
    val min_residues

    output:
    tuple( val(id), path('filtered_pdbs/*.pdb', optional: true) )

    script:
    """
    mkdir filtered_pdbs
    for pdb_file in *.pdb; do

        pdb_wc \$pdb_file > pdb_info.txt

        model_count=\$(grep 'No. models:' pdb_info.txt | head -n 1 | awk '{print \$3}')
        if [ \$model_count -ne 1 ]; then
            echo "WARNING: skipping \$pdb_file, more than one model."
            continue
        fi

        chain_count=\$(grep 'No. chains:' pdb_info.txt | head -n 1 | awk '{print \$3}')
        if [ \$chain_count -ne 1 ]; then
            echo "WARNING: skipping \$pdb_file, more than one chain."
            continue
        fi

        residue_count=\$(grep 'No. residues:' pdb_info.txt | head -n 1 | awk '{print \$3}')
        if [ \$residue_count -gt ${min_residues} ]; then
            ln -s "../\$pdb_file" filtered_pdbs/
        else
            echo "WARNING: Skipping \$pdb_file, less than ${min_residues} residues."
        fi
    done
    """
}
