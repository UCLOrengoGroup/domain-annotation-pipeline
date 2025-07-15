process extract_pdb_from_zip {
    container 'domain-annotation-pipeline-pdb-tools'

    input:
    path id_file
    path pdb_zip

    output:
    path '*.pdb'

    script:
    """
    awk '{print \$0 ".pdb"}' ${id_file} > pdb_list.txt
    unzip ${pdb_zip} \$(cat pdb_list.txt)
    """
}
