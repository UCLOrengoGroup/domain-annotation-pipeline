process fetch_foldseek_assets {
    label 'sge_low'
    storeDir "${params.cache_dir}"
    
    output:
    path "foldseekdb", emit: target_db
    path "CathDomainList.S95.v4.4.0", emit: lookup_file

    script:
    """
    echo "Downloading foldseek database for URL: ${params.foldseek_db_url}"
    echo "Cache directory: ${params.cache_dir}"
    
    wget -O foldseekdb.tar.gz "${params.foldseek_db_url}"
    tar -xzf foldseekdb.tar.gz
    rm -f foldseekdb.tar.gz

    wget -O "CathDomainList.S95.v4.4.0" "${params.foldseek_lookup_url}"
    
    echo "Download complete"
    """
}
