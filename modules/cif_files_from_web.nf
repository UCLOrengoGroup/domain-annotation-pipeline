process cif_files_from_web {
    input:
    path 'af_ids.txt'

    output:
    path 'AF-*.cif'
    publishDir './results/cifs' , mode: 'copy'

    script:
    """
    awk '{print "${params.alphafold_url_stem}/"\$1".cif"}' af_ids.txt > af_model_urls.txt
    wget -i af_model_urls.txt || true
    """
}