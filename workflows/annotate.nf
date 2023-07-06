#!/usr/bin/env nextflow
nextflow.enable.dsl=2

// the number of uniprot ids processed in each chunk of work 
params.chunk_size = 3

params.cath_version = 'v4_3_0'

params.af_version = 4

params.uniprot_csv_file = "${workflow.launchDir}/data/uniprot_ids.csv"
params.alphafold_url_stem = "https://alphafold.ebi.ac.uk/files"


process cif_files_from_web {
    input:
    path 'af_ids.txt'

    output:
    path 'AF-*.cif'

    """
    awk '{print "${params.alphafold_url_stem}/"\$1".cif"}' af_ids.txt > af_model_urls.txt
    wget -i af_model_urls.txt || true
    """
}

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


process cif_to_pdb {
    container 'domain-annotation-pipeline-pdb-tools'

    input:
    path '*'

    output:
    path '*.pdb'

    """
    for cif_file in *.cif; do
        pdb_file=\${cif_file%.cif}.pdb
        pdb_fromcif \$cif_file > \$pdb_file
    done
    """
}

process run_chainsaw {
    container 'domain-annotation-pipeline-chainsaw'
    stageInMode 'copy'
    input:
    path '*'

    output:
    path 'chainsaw_results.csv'

    """
    ${params.chainsaw_script} --structure_directory . -o chainsaw_results.csv
    sed -i '/^chain_id/d' chainsaw_results.csv
    """
}

process run_merizo {
    container 'domain-annotation-pipeline-merizo'
    stageInMode 'copy'

    input:
    path '*'

    output:
    path 'merizo_results.csv'

    """
    ${params.merizo_script} -d cpu -i *.pdb > merizo_results.csv
    """
}

process run_unidoc {
    container 'domain-annotation-pipeline-unidoc'

    input:
    path '*'

    output:
    path 'unidoc_results.csv'

    """
    # UniDoc expects to be run from its own directory
    ln -s ${params.unidoc_dir}/bin bin

    for pdb_file in *.pdb; do
        file_stem=\${pdb_file%.pdb}

        ${params.unidoc_script} -i \$pdb_file -c A -o \${file_stem}.unidoc

        # extract the chopping from the last line of the unidoc output (possibly blank)
        # and change chopping string to the expected format
        chopping=\$(tail -n 1 \${file_stem}.unidoc | tr '~' '-' | tr ',' '_' | tr '/' ',' | tr -d '\\n')

        echo "\$file_stem\t\$chopping" >> unidoc_results.csv
    done
    """
}

process run_measure_globularity {
    input:
    path 'af_domain_list.csv'
    path '*.cif'

    output:
    path 'af_domain_globularity.csv'

    """
    cath-af-cli measure-globularity \
        --af_domain_list af_domain_list.csv \
        --af_chain_mmcif_dir . \
        --af_domain_globularity af_domain_globularity.csv \
    """
}

process collect_results {
    input:
    file 'chainsaw_results.tsv'
    file 'merizo_results.tsv'
    file 'unidoc_results.tsv'

    output:
    file 'all_results.tsv'

    """
    ${params.combine_script} \
        -m merizo_results.tsv \
        -u unidoc_results.tsv \
        -c chainsaw_results.tsv \
        -o all_results.tsv
    """
}

workflow {

    // Create a channel from the uniprot csv file
    def uniprot_ids_ch = Channel.fromPath( params.uniprot_csv_file )
        // process the file as a CSV with a header line
        .splitCsv(header: true)
        // only process a few ids when debugging
        .take( 5 )

    // Generate files containing chunks of AlphaFold ids
    // NOTE: this will only retrieve the first fragment in the AF prediction (F1)
    def af_ids = uniprot_ids_ch
        // make sure we don't have duplicate uniprot ids
        .unique()
        // map uniprot id (CSV row) to AlphaFold id
        .map { up_row -> "AF-${up_row.uniprot_id}-F1-model_v${params.af_version}" }
        // collect all ids into a single file
        .collectFile(name: 'all_af_ids.txt', newLine: true)
        // split into chunks and save to files
        .splitText(file: 'chunked_af_ids.txt', by: params.chunk_size)

    // download cif files
    // def cif_ch = cif_files_from_gs( af_ids )
    def cif_ch = cif_files_from_web( af_ids )

    // convert cif to pdb files
    def pdb_ch = cif_to_pdb( cif_ch )

    // run chainsaw on the pdb files
    def chainsaw_results_ch = run_chainsaw( pdb_ch )

    // run merizo on the pdb files
    def merizo_results_ch = run_merizo( pdb_ch )

    // run unidoc on the pdb files
    def unidoc_results_ch = run_unidoc( pdb_ch )

    def all_chainsaw_results = chainsaw_results_ch
        .collectFile(name: 'domain_assignments.chainsaw.tsv', 
            storeDir: workflow.launchDir)

    def all_merizo_results = merizo_results_ch
        .collectFile(name: 'domain_assignments.merizo.tsv', 
            storeDir: workflow.launchDir)

    def all_unidoc_results = unidoc_results_ch
        .collectFile(name: 'domain_assignments.unidoc.tsv', 
            storeDir: workflow.launchDir)
    
    def all_results = collect_results( 
            all_chainsaw_results, 
            all_merizo_results, 
            all_unidoc_results 
        )
        .collectFile(name: 'domain_assignments.tsv', 
             // skip: 1,
            storeDir: workflow.launchDir)
        .subscribe {
            println "All results: $it"
        }
}