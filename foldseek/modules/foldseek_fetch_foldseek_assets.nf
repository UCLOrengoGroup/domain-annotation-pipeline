process fetch_foldseek_assets {
    label 'sge_low'
    // Use storeDir for local, publishDir for CI
    storeDir params.ci_mode ? null : "${params.cache_dir}" // storeDir "${params.cache_dir}"
    publishDir params.ci_mode ? "${params.cache_dir}" : "${params.cache_dir}", mode: 'copy', enabled: params.ci_mode
    
    output:
    path "foldseekdb", emit: target_db
    path "CathDomainList.S95.v4.4.0", emit: lookup_file

    script:
    """
    echo "Downloading foldseek database for URL: ${params.foldseek_db_url}"
    echo "Cache directory: ${params.cache_dir}"
    echo "CI mode: ${params.ci_mode}"
    
    wget -O foldseekdb.tar.gz "${params.foldseek_db_url}"
    tar -xzf foldseekdb.tar.gz
    rm -f foldseekdb.tar.gz

    wget -O "CathDomainList.S95.v4.4.0" "${params.foldseek_lookup_url}"
    
    echo "Download complete"
    """
}
