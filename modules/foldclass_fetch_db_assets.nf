process fetch_foldclass_assets {
    label 'sge_low'

    // Use storeDir for local, publishDir for GH CI run
    storeDir params.ci_mode ? null : "${params.foldclass_db_dir}"
    publishDir "${params.foldclass_db_dir}", mode: 'copy', enabled: params.ci_mode

    output:
    path "cath_s95_v4.4.0_class123_foldclass_db.pt", emit: reference_db
    path "cath_s95_v4.4.0_class123_foldclass_db.targets", emit: targets_list

    script:
    """
    echo "Downloading Foldclass database from URL: ${params.foldclass_db_url}"
    echo "Cache directory: ${params.foldclass_db_dir}"
    echo "CI mode: ${params.ci_mode}"

    wget -O "cath_s95_v4.4.0_class123_foldclass_db.pt" "${params.foldclass_db_url}"
    wget -O "cath_s95_v4.4.0_class123_foldclass_db.targets" "${params.foldclass_targets_url}"

    echo "Download complete"
    """
}
