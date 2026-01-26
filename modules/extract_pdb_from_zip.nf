process extract_pdb_from_zip {
    label 'sge_low'
    container 'domain-annotation-pipeline-ted-tools'

    input:
    tuple( val(id), path(id_file) )
    path pdb_zip

    output:
    tuple( val(id), path('*.pdb') )

    script:
    """
    awk '{print \$0 ".pdb"}' ${id_file} > pdb_list.txt
    while read -r fname; do
        unzip ${pdb_zip} "\$fname"
    done < pdb_list.txt
    """
}
