#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

/*
 * Domain Annotation Pipeline - Main Workflow
 * 
 * This workflow processes UniProt entries through multiple domain prediction tools,
 * generates consensus results, and produces final annotated domain assignments.
 */


// ===============================================
// PARAMETERS
// ===============================================
// Output directory
params.results_dir = "${workflow.launchDir}/results/${params.project_name}"
params.publish_mode = 'copy'

// ===============================================
// MODULE IMPORTS
// ===============================================

// Data preparation modules
include { get_uniprot_data } from '../modules/get_uniprot.nf'
include { collect_taxonomy } from '../modules/collect_taxonomy.nf'
//can delete line - unused process.
include { extract_pdb_from_zip } from '../modules/extract_pdb_from_zip.nf'
include { filter_pdb } from '../modules/filter_pdb.nf'

// Domain prediction modules
// include { run_chainsaw } from '../modules/run_chainsaw.nf'
// include { run_merizo } from '../modules/run_merizo.nf'
// include { run_unidoc } from '../modules/run_unidoc.nf'
include { run_ted_segmentation } from '../modules/run_ted_segmentation.nf'

// Filtering and consensus modules
include { run_filter_domains } from '../modules/run_filter_domains.nf'
include { run_filter_domains_reformatted as run_filter_domains_reformatted_unidoc } from '../modules/run_filter_domains_reformatted.nf'
include { run_filter_domains_reformatted as run_filter_domains_reformatted_merizo } from '../modules/run_filter_domains_reformatted.nf'
include { convert_merizo_results } from '../modules/convert_merizo_results.nf'
include { convert_unidoc_results } from '../modules/convert_unidoc_results.nf'
include { run_get_consensus } from '../modules/run_get_consensus.nf'
include { run_filter_consensus } from '../modules/run_filter_consensus.nf'

// Post-processing modules
include { chop_pdb } from '../modules/chop_pdb.nf'
include { chop_pdb_from_zip } from '../modules/chop_pdb_from_zip.nf'
include { create_md5 } from '../modules/create_domain_md5.nf'
include { run_stride } from '../modules/run_stride.nf'
include { summarise_stride } from '../modules/summarise_stride.nf'
include { transform_consensus } from '../modules/transform.nf'

// Analysis modules
include { run_measure_globularity } from '../modules/run_measure_globularity.nf'
include { run_plddt } from '../modules/run_plddt.nf'
include { join_plddt_md5 } from '../modules/join_plddt_md5.nf'

// Final collection modules
include { collect_results } from '../modules/collect_results_combine_chopping.nf'
include { collect_results_final } from '../modules/collect_results_add_metadata.nf'
include { run_AF_domain_id } from '../modules/run_create_AF_domain_id.nf'

// Foldseek modules
include { foldseek_create_db } from '../foldseek/modules/foldseek_create_db.nf'
include { foldseek_run_foldseek } from '../foldseek/modules/foldseek_run_foldseek.nf'
include { foldseek_run_convertalis } from '../foldseek/modules/foldseek_run_convertalis.nf'
include { foldseek_process_results } from '../foldseek/modules/foldseek_process_results.nf'


// ===============================================
// HELPER FUNCTIONS
// ===============================================

def validateParameters() {

    if (!params.project_name) {
        error("Project name must be specified in the parameters.")
    }

    if (!params.chunk_size || params.chunk_size <= 0) {
        error("Chunk size must be a positive integer.")
    }

    if (params.debug && !params.max_entries) {
        params.max_entries = 10
    }

    if (!params.uniprot_csv_file || !params.pdb_zip_file) {
        error("Both UniProt CSV file and PDB ZIP file must be specified.")
    }

    // Ensure results directory exists
    if (!file(params.results_dir).exists()) {
        file(params.results_dir).mkdirs()
    }

    // Validate required parameters
    if (!params.uniprot_csv_file || !file(params.uniprot_csv_file).exists()) {
        error("UniProt CSV file not found: ${params.uniprot_csv_file}")
    }
    if (!params.pdb_zip_file || !file(params.pdb_zip_file).exists()) {
        error("PDB ZIP file not found: ${params.pdb_zip_file}")
    }

    log.info(
        """
    ==============================================
    Domain Annotation Pipeline
    ==============================================
    Project name        : ${params.project_name}
    UniProt CSV file    : ${params.uniprot_csv_file}
    PDB ZIP file        : ${params.pdb_zip_file}
    Main chunk size     : ${params.chunk_size}
    Light chunk size    : ${params.light_chunk_size}
    Heavy chunk size    : ${params.heavy_chunk_size}
    Min chain residues  : ${params.min_chain_residues}
    Max entries (debug) : ${params.max_entries ?: 'N/A'}
    Results dir         : ${params.results_dir}
    Debug mode          : ${params.debug}
    ==============================================
    """.stripIndent()
    )
}

// ===============================================
// MAIN WORKFLOW
// ===============================================

workflow {

    validateParameters()
    file("${params.results_dir}/consensus_chunks").mkdirs()

    // =========================================
    // PHASE 1: Data Preparation
    // =========================================

    // Create UniProt ID channel
    uniprot_ids_ch = Channel.fromPath(params.uniprot_csv_file, checkIfExists: true)
        .splitText()
        .map { it.trim() }
        .filter { it != ''}
        .unique()

    // Apply debug limit if enabled
    if (params.debug && params.max_entries) {
        uniprot_ids_ch = uniprot_ids_ch.take(params.max_entries)
    }

    // Create chunked AF IDs for processing
    chunked_af_ids_ch = uniprot_ids_ch
        .collectFile(
            name: 'all_af_ids.txt',
            newLine: true,
            storeDir: "${params.results_dir}/intermediate",
        )
        .splitText(by: params.chunk_size, file: true)
        .toList()
        .flatMap { List chunk_files ->
            // Emit a tuple (id, path) where id is the chunk index and path is the chunk file
            chunk_files.withIndex().collect { cf, idx ->
                [ idx, cf ]
            }
        }

    // Get taxonomic data
    uniprot_data_ch = get_uniprot_data(chunked_af_ids_ch)
    collected_taxonomy_ch = uniprot_data_ch.collectFile(
        name: 'all_taxonomy.tsv',
        keepHeader: true,
        newLine: true,
        storeDir: params.results_dir,
        sort: { it -> it[0] } // sort by chunk id
    ) { it -> it[1] } // use file name to collect

    // af_ids_ch.view { "af_ids_ch: " + it }
    // chunked_af_ids_ch.view { "chunked_af_ids_ch: " + it }

    // Extract and filter PDB files
    // pass only the ID file path channel (af_ids_ch) to the extractor so it receives a path
    unfiltered_pdb_ch = extract_pdb_from_zip(chunked_af_ids_ch, file(params.pdb_zip_file))
    // unfiltered_pdb_ch = extract_pdb_from_zip(af_ids_ch, file(params.pdb_zip_file))
    filtered_pdb_ch = filter_pdb(unfiltered_pdb_ch, params.min_chain_residues)

    // TODO: currently the rest of the workflow uses channel without chunk index
    //       we should feed, this through to all subsequent steps for better
    //       tracking / debugging / caching
    af_ids_ch = chunked_af_ids_ch.map { it -> it[1] }
    filtered_pdb_ch = filtered_pdb_ch.map { it -> it[1] }

    // =========================================
    // PHASE 2: Domain Prediction
    // =========================================

    // deterministic chunking: collect & sort, then chunk
    // required for caching, but waits for all PDBs first
    heavy_chunk_ch = filtered_pdb_ch
        .flatten()
        .toSortedList { it.toString() } // sort PDB paths deterministically
        .flatMap { List allFiles ->
            def chunks = []
            def step = params.heavy_chunk_size as int
            for (int i = 0; i < allFiles.size(); i += step) {
                def end = Math.min(i + step, allFiles.size())
                chunks << allFiles.subList(i, end)
            }
            return chunks
        }

    segmentation_ch = run_ted_segmentation(heavy_chunk_ch)

    // =========================================
    // PHASE 3: Results Collection & Filtering
    // =========================================

    // collect the result for the chainsaw output
    collected_chainsaw_ch = segmentation_ch.chainsaw.collectFile(
        name: 'domain_assignments.chainsaw.tsv',
        storeDir: params.results_dir,
    )
    collected_merizo_ch = segmentation_ch.merizo.collectFile(
        name: 'domain_assignments.merizo.tsv',
        storeDir: params.results_dir,
    )
    collected_unidoc_ch = segmentation_ch.unidoc.collectFile(
        name: 'domain_assignments.unidoc.tsv',
        storeDir: params.results_dir,
    )
    collected_consensus_ch = segmentation_ch.consensus.collectFile(
        name: 'domain_assignments.consensus.tsv',
        storeDir: params.results_dir,
    )

    // =========================================
    // PHASE 4: Post-Consensus Processing
    // =========================================

    // Split consensus file into chunks for parallel processing using native Nextflow
    consensus_chunks_ch = collected_consensus_ch
        .splitText(
            by: params.light_chunk_size, 
            file: "${params.results_dir}/consensus_chunks/consensus_chunks"
        )
        .toList()
        .flatMap { List chunk_files ->
            // Emit a tuple (id, path) where id is the chunk index and path is the chunk file
            chunk_files.withIndex().collect { cf, idx ->
                [ idx, cf ]
            }
        }

    // Chop pdbs in parallel using chunks and extracting from zip on-the-fly
    chopped_pdb_ch = chop_pdb_from_zip(
        consensus_chunks_ch,
        file(params.pdb_zip_file)
    )
    // Generate MD5 hashes for domains added a new file and script_ch
    md5_chunks_ch = create_md5(chopped_pdb_ch)
    collected_md5_ch = md5_chunks_ch
        .collectFile(
            name: "all_md5.tsv",
            storeDir: params.results_dir,
            sort: { it -> it[0] } // sort by chunk id
        ) { it -> it[1] } // use file name to collect

    // =========================================
    // PHASE 5: Structure Analysis
    // =========================================

    // Run STRIDE analysis
    stride_results_ch = run_stride(chopped_pdb_ch)    
    stride_summaries_ch = summarise_stride(stride_results_ch)
    collected_stride_summaries_ch = stride_summaries_ch.collectFile(
        name: "all_stride_summaries.tsv",
        storeDir: params.results_dir,
        sort: { it -> it[0] } // sort by chunk id
    ) { it -> it[1] } // use file name to collect
    
    // Run globularity analysis
    globularity_ch = run_measure_globularity(chopped_pdb_ch)
    // globularity_ch.view { "globularity_ch: " + it }
    // no flatten as only a single file per chunk
    collected_globularity_ch = globularity_ch.collectFile(
        name: "all_domain_globularity.tsv",
        storeDir: params.results_dir,
        sort: { it -> it[0] } // sort by chunk id
    ) { it -> it[1] } // use file name to collect

    // chopped_pdb_ch.view { "chopped_pdb_ch: " + it }

    // Run pLDDT analysis
    plddt_ch = run_plddt(chopped_pdb_ch)
    // plddt_ch.view { "plddt_ch: " + it }
    // no flatten as only a single file per chunk
    collected_plddt_ch = plddt_ch.collectFile(
        name: "all_plddt.tsv",
        storeDir: params.results_dir,
        sort: { it -> it[0] } // sort by chunk id
    ) { it -> it[1] } // use file name to collect

    collected_plddt_with_md5_ch = join_plddt_md5(collected_plddt_ch, collected_md5_ch)

    // =========================================
    // PHASE 6: Run foldseek
    // =========================================

    // Create the query DB from the chopped pdbs
    foldseek_create_db(chopped_pdb_ch) // New - run stright off chopped_pdb output
    //chopped_pdb_ch
    //    .map { id, files -> files }  // ← Extract just the files
    //    .flatten()
    //    .collate(params.light_chunk_size)
    //    .set { pdb_chunks }
    //foldseek_create_db(pdb_chunks) // These 6 lines were removed

    // Define the target (CATH) database using config: params.target_db - .flatten()
    ch_target_db = Channel.fromPath(params.target_db) // Remains the same
    // Run foldseek search on the output of process create_foldseek_db and the CATH database
    fs_search_ch = foldseek_run_foldseek(foldseek_create_db.out.query_db_dir, ch_target_db) // just added the "fs_search_ch" channel
    
    // Convert results with fs convertalis, pass query_db, CATH_db and output db from run_foldseek
    //foldseek_run_convertalis(foldseek_run_foldseek.out.search_results, ch_target_db) - removed
    fs_m8_ch = foldseek_run_convertalis(fs_search_ch, ch_target_db) // Added to run from fs_search_ch and the fs_m8_ch at the start

    // Parse output - first create a channel from the location of the python script
    ch_parser_script = Channel.fromPath(params.parser_script, checkIfExists: true)
    ch_lookup_file = Channel.fromPath(params.lookup_file, checkIfExists: true)
    
    // Now pass the convertalis .m8 and the python script as intput to the parsing process
    //foldseek_process_results(foldseek_run_convertalis.out.m8_output, ch_lookup_file, ch_parser_script) - removed
    fs_parsed_ch = foldseek_process_results(fs_m8_ch, ch_lookup_file, ch_parser_script) // changed to run on fs_m8_ch and use fs_parsed_ch

    //foldseek_ch = foldseek_process_results.out.foldseek_parsed_results
    //    .collectFile(
    //    name: 'foldseek_parsed_results.tsv',
    //    keepHeader: true,
    //    skip: 1,
    //    sort: true,
    //    storeDir: "${params.results_dir}"
    //    ) // Removed these 8 lines
    foldseek_ch = fs_parsed_ch.collectFile( // Added these lines to match other collectFile statements
        name: 'foldseek_parsed_results.tsv',
        keepHeader: true,
        skip: 1,
        storeDir: params.results_dir,
        sort: { it -> it[0] }
    ) { it -> it[1] }

    // =========================================
    // PHASE 8: Final Assembly
    // =========================================

    // Transform consensus with structure data
    transformed_consensus_ch = transform_consensus(
        collected_consensus_ch,
        collected_md5_ch,
        collected_stride_summaries_ch,
    )

    // Generate AF domain IDs
    // af_domain_ids_ch = run_AF_domain_id(transformed_consensus_ch)

    // Collect intermediate results
    intermediate_results_ch = collect_results(
        collected_chainsaw_ch,
        collected_merizo_ch,
        collected_unidoc_ch,
        
    )

    // Generate final comprehensive results
    final_results_ch = collect_results_final(
        transformed_consensus_ch,
        collected_globularity_ch,
        collected_plddt_with_md5_ch,
        collected_taxonomy_ch,
        foldseek_ch,
    )

    // =========================================
    // PHASE 9: Output Generation
    // =========================================

    // Ensure final outputs are saved
    final_results_ch
        .map { file ->
            def output_path = "${params.results_dir}/final_domain_annotations.tsv"
            file.copyTo(output_path)
            log.info("Final results written to: ${output_path}")
            return output_path
        }
        .view { "Final output: ${it}" }

    // Create completion marker
    final_results_ch
        .map {
            def completion_file = file("${params.results_dir}/WORKFLOW_COMPLETED")
            completion_file.text = """
            Workflow completed successfully at: ${new Date()}
            Total processing time: ${workflow.duration}
            """.stripIndent()
            return "Workflow completed successfully"
        }
        .view()
}
