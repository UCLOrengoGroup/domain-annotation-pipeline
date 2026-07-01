process extract_pdb_from_tar {
    label 'sge_gpu_high'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}" 
    publishDir './results/pdbs', mode: 'copy'

    input:
    path id_file
    path pdb_tar

    output:
    path '*.pdb'

    script:
    """
    awk '{print "./" \$0 ".pdb"}' ${id_file} > pdb_list.txt
    tar -xzf ${pdb_tar} -T pdb_list.txt
    """
}
