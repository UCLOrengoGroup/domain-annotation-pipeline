process fetch_contrasted_assets {
    label 'sge_low'
    // Use storeDir for local, publishDir for CI
    storeDir params.ci_mode ? null : "${params.conted_db_dir}"
    publishDir "${params.conted_db_dir}", mode: 'copy', enabled: params.ci_mode
    
    output:
    path "S95-v4_4_0.pt", emit: reference_db
    path "cath-domain-sf-list.txt", emit: domain_list

    script:
    """
    echo "Downloading contrasted database for URL: ${params.conted_db_url}"
    echo "Cache directory: ${params.conted_db_dir}"
    echo "CI mode: ${params.ci_mode}"
    
    wget -O S95-v4_4_0_contrasted.tar.gz "${params.conted_db_url}"
    tar -xzf S95-v4_4_0_contrasted.tar.gz
    rm -f S95-v4_4_0_contrasted.tar.gz

    wget -O "cath-domain-sf-list.txt" "${params.conted_list_url}"
    
    echo "Download complete"
    """
}
