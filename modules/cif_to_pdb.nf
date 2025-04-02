process cif_to_pdb {
    container 'domain-annotation-pipeline-pdb-tools'

    input:
    path '*'

    output:
    path '*.pdb'

    script:
    """
    for cif_file in *.cif; do
        pdb_file=\${cif_file%.cif}.pdb
        pdb_fromcif \$cif_file > \$pdb_file
    done
    """
}