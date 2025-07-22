process extract_pdb_from_zip {
    label 'sge_low'
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
    
    # Filter for those with >=25 residues (based on CA atoms)
    for file in *.pdb; do
        count=\$(awk '\$1 == "ATOM" && \$3 == "CA" { print \$4 "_" \$6 }' \$file | sort -u | wc -l)
        if [ \$count -lt 25 ]; then
            echo "Filtered out \$file — only \$count residues"
            rm \$file
        fi
    done
    """
}
