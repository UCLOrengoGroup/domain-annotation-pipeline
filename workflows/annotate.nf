#!/usr/bin/env nextflow
include { cif_files_from_web }      from './modules/cif_files_from_web.nf'
include { cif_files_from_gs }       from './modules/cif_files_from_gs.nf'
include { cif_to_pdb }              from './modules/cif_to_pdb.nf'
include { run_chainsaw }            from './modules/run_chainsaw.nf'
include { run_merizo }              from './modules/run_merizo.nf'
include { run_unidoc }              from './modules/run_unidoc.nf'
include { run_measure_globularity } from './modules/run_measure_globularity.nf'
include { collect_results }         from './modules/collect_results.nf'
include { runFilterDomains }        from './modules/runFilterDomains.nf'
include { collectChoppingNames }    from './modules/collectChoppingNames.nf'
include { runGetConsensus }         from './modules/runGetConsensus.nf'
include { runFilterConsensus }        from './modules/runFilterConsensus.nf'

workflow {

    // Create a channel from the uniprot csv file
    def uniprot_ids_ch = Channel.fromPath( params.uniprot_csv_file )
        // process the file as a CSV with a header line
        .splitCsv(header: true)
        // only process a few ids when debugging
        // .take( 5 )

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