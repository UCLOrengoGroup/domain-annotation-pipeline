// Not used
process cif_files_from_gs {
    input:
    path 'af_ids.txt'

    output:
    path "AF-*.cif", optional: true

    // If Google returns 401 errors then make sure you have logged in:
    // 
    // gcloud auth application-default login
    //
    // see: https://www.nextflow.io/docs/latest/google.html

    """
    awk '{print \$1".cif"}' uniprot_ids.txt > af_ids.txt
    cat af_model_urls.txt | (gsutil -o GSUtil:parallel_process_count=1 -m cp -I . || echo "Ignoring non-zero exit code: \$?")
    """
}