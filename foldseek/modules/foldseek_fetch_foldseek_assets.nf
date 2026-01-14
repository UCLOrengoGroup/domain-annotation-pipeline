process fetch_foldseek_assets {
    label 'sge_low'
    storeDir "${params.foldseek_assets_dir}"
    
    output:
    path "foldseekdb", emit: target_db
    path "CathDomainList.S95.v4.4.0", emit: lookup_file

    script:
    """
    # Check if DB exists in storeDir and symlink it, otherwise download
    if [ -d "${params.foldseek_assets_dir}/foldseekdb" ]; then
        echo "Foldseek database already exists, creating symlink..."
        ln -s "${params.foldseek_assets_dir}/foldseekdb" foldseekdb
    else
        echo "Downloading foldseek database..."
        wget -O foldseekdb.tar.gz "${params.foldseek_db_url}"
        tar -xzf foldseekdb.tar.gz
        rm -f foldseekdb.tar.gz
    fi

    # Check if lookup file exists in storeDir and symlink it, otherwise download
    if [ -f "${params.foldseek_assets_dir}/CathDomainList.S95.v4.4.0" ]; then
        echo "Lookup file already exists, creating symlink..."
        ln -s "${params.foldseek_assets_dir}/CathDomainList.S95.v4.4.0" CathDomainList.S95.v4.4.0
    else
        echo "Downloading lookup file..."
        wget -O "CathDomainList.S95.v4.4.0" "${params.foldseek_lookup_url}"
    fi
    """
}
