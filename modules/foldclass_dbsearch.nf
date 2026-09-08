process foldclass_run_dbsearch {
    label 'sge_low'
    //container "ghcr.io/uclorengogroup/domain-annotation-pipeline-ted-tools:${params.container_tag_name}"
    container "domain-annotation-pipeline-ted-tools:latest"

    input:
    tuple val(id), path(chopped_pdb_tar_file)
    path reference_db // This is the cath_s95_v4.4.0_class123_foldclass_db.pt file
    path targets_list // This is the cath_s95_v4.4.0_class123_foldclass_db.targets file

    output:
    tuple val(id), path("${id}_foldclass.tsv"), emit: foldclass_annotations

    script:
    // cath_s95_v4.4.0_class123_foldclass_db is passed to pytorch_foldclass_dbsearch.py which automatically opens the .pt and .targets file
    """
    mkdir -p pdb

    tar -xzf ${chopped_pdb_tar_file} -C pdb

    python /app/ted-tools/foldclass/embed/pytorch_foldclass_dbsearch.py \
        -n cath_s95_v4.4.0_class123_foldclass_db \
        pdb/*.pdb \
        > ${id}_foldclass.tsv
    """
}