#!/usr/bin/env nextflow
params.uniprot_csv_file = "${workflow.projectDir}/../assets/uniprot_ids.csv"
params.pdb_tar_file = "${workflow.projectDir}/../assets/bfvd.tar.gz"
params.chunk_size = 3        // the number of uniprot ids processed in each chunk of work 
params.cath_version = 'v4_3_0'
nextflow.enable.dsl=2
// params for the chopping consensus programs
params.chopping_file = "../domain_assignments.chaninsaw.tsv"
params.reformatted_file_meriz = "../results/merizo_results_refomatted.tsv"
params.reformatted_file_uni =   "../results/unidoc_results_reformatted.tsv"

include { get_uniprot_data }        from '../modules/get_uniprot.nf'
include { collect_taxonomy }        from '../modules/collect_taxonomy.nf'
include { extract_pdb }             from '../modules/extract_pdb.nf'
include { run_chainsaw }            from '../modules/run_chainsaw.nf'
include { run_merizo }              from '../modules/run_merizo.nf'
include { run_unidoc }              from '../modules/run_unidoc.nf'
include { collect_results }         from '../modules/collect_results_combine_chopping.nf'
include { convert_files }           from '../modules/convert_files.nf'
include { run_filter_domains }        from '../modules/run_filter_domains.nf'
include { run_filter_domains_reformatted } from '../modules/run_filter_domains_reformatted.nf'
include { collect_chopping_names }  from '../modules/collect_chopping_names.nf'
include { run_get_consensus }       from '../modules/run_get_consensus.nf'
include { run_filter_consensus }    from '../modules/run_filter_consensus.nf'
include { chop_pdb }                from '../modules/chop_pdb.nf'
include { transform_consensus }     from '../modules/transform.nf'
include { run_stride }              from '../modules/run_stride.nf'
include { create_md5 }              from '../modules/create_domain_md5.nf'
include { summarise_stride }        from '../modules/summarise_stride.nf'
include { run_measure_globularity } from '../modules/run_measure_globularity.nf'
include { run_AF_domain_id }        from '../modules/run_create_AF_domain_id.nf'
include { run_plddt }               from '../modules/run_plddt.nf'
include { join_plddt_md5 }          from '../modules/join_plddt_md5.nf'
include { collect_results_final }   from '../modules/collect_results_add_metadata.nf'

workflow {

    // Create a channel from the uniprot csv file
    def uniprot_ids_ch = Channel.fromPath( params.uniprot_csv_file )
        .splitCsv(header: true)  // process the file as a CSV with a header line
        // .take( 5 ) //only process a few ids when debugging
    def uniprot_rows_ch = Channel.fromPath( params.uniprot_csv_file )
        .splitCsv(header: true)
        .map { row -> row.uniprot_id }
        get_uniprot_data(uniprot_rows_ch)  // Get taxonomic data from uniprot
    def taxonomy = collect_taxonomy(get_uniprot_data.out.collect()) // Collect into a single output file
    // Generate files containing chunks of ids.
    def af_ids = uniprot_ids_ch
        .map { row -> row.uniprot_id }   // get just the uniprot ID string
        .unique()
        .collectFile(name: 'all_af_ids.txt', newLine: true)
        .splitText(file: 'chunked_af_ids.txt', by: params.chunk_size)

    // extract pdbs from the databse tar.gz file
    def pdb_ch = extract_pdb( af_ids, file( params.pdb_tar_file ))

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
    def md5 = create_md5(chop.chop_files.flatten())             // creates an domain-level md5 has from the seq in the chopped pdb files
    def combined_md5 = md5.collectFile(name: "all_md5.tsv", sort: true)
    def stride = run_stride(chop.chop_files)                    // Run STRIDE on each chopped pdb domain file
    def globularity = run_measure_globularity(chop.chop_dir)    // Run globularity in the chopped pdb files
    def summaries = summarise_stride(stride.flatten())          // Summarise the STRIDE output
    def transform = transform_consensus(consensus.filtered, combined_md5, summaries.collect()) // Transformm filtered_consensus.tvs to transformed_consensus.tsv and add stride SSE
    def AF_Dom_id = run_AF_domain_id(transform)                 // Run the awk script to create eg. AF-ABC000-F1-model_v4/1-100 from the ted_id and chopping in transformed_consensus.tsv
    def plddt = run_plddt(chop.chop_dir)                     // Run fetch_avg_plddt.py on the chopped pdb files
    def merged_plddt = join_plddt_md5(plddt, combined_md5)
    // continue with the collect results process
    def all_results = collect_results( 
            all_chainsaw_results, 
            all_merizo_results, 
            all_unidoc_results 
        )
    def final_results = collect_results_final( 
            transform, 
            globularity, 
            merged_plddt,
            taxonomy 
        )
        
        combined_md5
            .map {file -> file.copyTo("${params.results_dir}/all_md5.tsv")}
            .subscribe {}
}