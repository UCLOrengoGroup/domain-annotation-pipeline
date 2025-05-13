#!/usr/bin/env nextflow
params.alphafold_url_stem = "https://alphafold.ebi.ac.uk/files"
params.uniprot_csv_file = "${workflow.projectDir}/../assets/uniprot_ids.csv"
params.chunk_size = 3        // the number of uniprot ids processed in each chunk of work 
params.cath_version = 'v4_3_0'
params.af_version = 4
nextflow.enable.dsl=2
// params for the chopping consensus programs
params.chopping_file = "../domain_assignments.chaninsaw.tsv"
params.reformatted_file_meriz = "../results/merizo_results_refomatted.tsv"
params.reformatted_file_uni =   "../results/unidoc_results_reformatted.tsv"

include { cif_files_from_web }      from '../modules/cif_files_from_web.nf'
include { cif_files_from_gs }       from '../modules/cif_files_from_gs.nf'
include { cif_to_pdb }              from '../modules/cif_to_pdb.nf'
include { run_chainsaw }            from '../modules/run_chainsaw.nf'
include { run_merizo }              from '../modules/run_merizo.nf'
include { run_unidoc }              from '../modules/run_unidoc.nf'
include { collect_results }         from '../modules/collect_results.nf'
include { convert_files }           from '../modules/convert_files.nf'
include { run_filter_domains }        from '../modules/run_filter_domains.nf'
include { run_filter_domains_reformatted } from '../modules/run_filter_domains_reformatted.nf'
include { collect_chopping_names }  from '../modules/collect_chopping_names.nf'
include { run_get_consensus }       from '../modules/run_get_consensus.nf'
include { run_filter_consensus }    from '../modules/run_filter_consensus.nf'
include { chop_pdb }                from '../modules/chop_pdb.nf'
include { transform_consensus }     from '../modules/transform.nf'
include { run_stride }              from '../modules/run_stride.nf'
include { summarise_stride }        from '../modules/summarise_stride.nf'
include { run_measure_globularity } from '../modules/run_measure_globularity.nf'
include { run_AF_Domain_id }        from '../modules/run_create_AF_Domain_id.nf'
include { run_plddt }               from '../modules/run_plddt.nf'
include { collect_results_final }   from '../modules/collect_results_final.nf'

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

    // Adding the filter and consensus processe to run in parallel with the collect results process
    def all_chainsaw_results = chainsaw_results_ch
        .collectFile(name: 'domain_assignments.chainsaw.tsv', 
            storeDir: workflow.launchDir)
    def chain_filter = run_filter_domains(all_chainsaw_results) // filter chainsaw results for inclusion in consensus

    def all_merizo_results = merizo_results_ch
        .collectFile(name: 'domain_assignments.merizo.tsv', 
            storeDir: workflow.launchDir)

    def all_unidoc_results = unidoc_results_ch
        .collectFile(name: 'domain_assignments.unidoc.tsv', 
            storeDir: workflow.launchDir)
    // convert the merizo and unidocs to include all 6 columns using the chainsaw results as a template
    def all_convert_results = convert_files(
            all_chainsaw_results,
            all_merizo_results,
            all_unidoc_results
    )
    def meriz_uni_filter = run_filter_domains_reformatted(all_convert_results)  // filter the newly formatted merizo and unidoc results
            run_get_consensus(chain_filter, meriz_uni_filter)   // create consensus results
    def consensus = run_filter_consensus(run_get_consensus.out) // run the post-consensus filtering process
    def chop = chop_pdb(consensus.filtered, pdb_ch.collect())   //Use filtered_consensus.tsv to chop the pdb files accordingly
    def stride = run_stride(chop)                               // Run STRIDE on each chopped pdb domain file
    def globularity = run_measure_globularity(chop.collect())   // Run globularity in the chopped pdb files
    def summaries = summarise_stride(stride.flatten())          // Summarise the STRIDE output
    def transform = transform_consensus(consensus.filtered, summaries.collect()) // Transformm filtered_consensus.tvs to transformed_consensus.tsv and add stride SSE
    def AF_Dom_id = run_AF_Domain_id(transform)                 // Run the awk script to create eg. AF-ABC000-F1-model_v4/1-100 from the ted_id and chopping in transformed_consensus.tsv
    def plddt = run_plddt(cif_ch.collect(), AF_Dom_id)          // Run convert-cif-to-plddt-summary on the original cif files with the choppings defined in transformed_consensus
    // continue with the collect results process
    def all_results = collect_results( 
            all_chainsaw_results, 
            all_merizo_results, 
            all_unidoc_results 
        )
    def final_results = collect_results_final( 
            transform, 
            globularity, 
            plddt 
        )
        //.collectFile(name: 'domain_assignments.tsv',  This looks unnecessary - changed to write directly to ./results/domain_sssignments.tsv in the collect_results process
             // skip: 1,
        //    storeDir: workflow.launchDir)
        //.subscribe {
        //    println "All results: $it"
        //}
}