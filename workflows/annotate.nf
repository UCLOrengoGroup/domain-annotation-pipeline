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
include { extract_pdb_from_zip } from '../modules/extract_pdb_from_zip.nf'
include { filter_pdb } from '../modules/filter_pdb.nf'

// Domain prediction modules
include { run_chainsaw } from '../modules/run_chainsaw.nf'
include { run_merizo } from '../modules/run_merizo.nf'
include { run_unidoc } from '../modules/run_unidoc.nf'

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

    // =========================================
    // PHASE 1: Data Preparation
    // =========================================

    // Create UniProt ID channel
    uniprot_ids_ch = Channel.fromPath(params.uniprot_csv_file, checkIfExists: true)
        .splitCsv(header: true)
        .map { row -> row.uniprot_id }
        .unique()

    // Apply debug limit if enabled
    if (params.debug && params.max_entries) {
        uniprot_ids_ch = uniprot_ids_ch.take(params.max_entries)
    }

    // Create chunked AF IDs for processing
    af_ids_ch = uniprot_ids_ch
        .collectFile(
            name: 'all_af_ids.txt',
            newLine: true,
            storeDir: "${params.results_dir}/intermediate",
        )
        .splitText(by: params.chunk_size, file: true)

    // Get taxonomic data
    uniprot_data_ch = get_uniprot_data(af_ids_ch)
    taxonomy_ch = uniprot_data_ch.collectFile(
        name: 'uniprot_data.tsv',
        keepHeader: true,
        newLine: true,
        storeDir: params.results_dir,
    )

    // Extract and filter PDB files
    unfiltered_pdb_ch = extract_pdb_from_zip(af_ids_ch, file(params.pdb_zip_file))
    filtered_pdb_ch = filter_pdb(unfiltered_pdb_ch, params.min_chain_residues)

    // =========================================
    // PHASE 2: Domain Prediction
    // =========================================

    // Run domain prediction tools in parallel
    heavy_chunk_ch = filtered_pdb_ch
        .flatten()
        .collate(params.heavy_chunk_size)
    chainsaw_results_ch = run_chainsaw(heavy_chunk_ch)
    merizo_results_ch = run_merizo(heavy_chunk_ch)
    unidoc_results_ch = run_unidoc(filtered_pdb_ch)

    // =========================================
    // PHASE 3: Results Collection & Filtering
    // =========================================

    // Collect all domain prediction results
    collected_chainsaw_ch = chainsaw_results_ch.collectFile(
        name: 'domain_assignments.chainsaw.tsv',
        storeDir: params.results_dir,
    )

    collected_merizo_ch = merizo_results_ch.collectFile(
        name: 'domain_assignments.merizo.tsv',
        storeDir: params.results_dir,
    )

    collected_unidoc_ch = unidoc_results_ch.collectFile(
        name: 'domain_assignments.unidoc.tsv',
        storeDir: params.results_dir,
    )

    // Filter chainsaw results
    filtered_chainsaw_ch = run_filter_domains(collected_chainsaw_ch)

    // Convert and filter merizo/unidoc results
    converted_merizo_results_ch = convert_merizo_results(
        collected_chainsaw_ch,
        collected_merizo_ch,
    )
    converted_unidoc_results_ch = convert_unidoc_results(
        collected_chainsaw_ch,
        collected_unidoc_ch,
    )

    filtered_converted_merizo_results_ch = run_filter_domains_reformatted_merizo(
        converted_merizo_results_ch
    )

    filtered_converted_unidoc_results_ch = run_filter_domains_reformatted_unidoc(
        converted_unidoc_results_ch
    )

    // =========================================
    // PHASE 4: Consensus Generation
    // =========================================

    // Generate consensus from filtered results
    consensus_raw_ch = run_get_consensus(
        filtered_chainsaw_ch,
        filtered_converted_merizo_results_ch.flatten().collect(),
        filtered_converted_unidoc_results_ch.flatten().collect(),
    )

    consensus_filtered_ch = run_filter_consensus(consensus_raw_ch)

    // =========================================
    // PHASE 5: Post-Consensus Processing
    // =========================================

    // Chop pdbs using pdb files:
    chopped_pdb_ch = chop_pdb(
        consensus_filtered_ch.filtered,
        filtered_pdb_ch.collect(),
    )

    // Generate MD5 hashes for domains
    md5_individual_ch = create_md5(chopped_pdb_ch
        .flatten()
        .collate(params.light_chunk_size)   // Changed to light chunk size
    )
    md5_combined_ch = md5_individual_ch
        .flatten()
        .collectFile(
        name: "all_md5.tsv",
        sort: true,
        storeDir: params.results_dir,
        )

    // =========================================
    // PHASE 6: Structure Analysis
    // =========================================

    // Run STRIDE analysis
    stride_results_ch = run_stride(chopped_pdb_ch)
    stride_summaries_ch = summarise_stride(stride_results_ch
        .flatten()
        .collate(params.light_chunk_size))  // Changed to light chunksize

    // Run globularity analysis
    globularity_ch = run_measure_globularity(chopped_pdb_ch)

    // Run pLDDT analysis
    plddt_ch = run_plddt(chopped_pdb_ch)
    plddt_with_md5_ch = join_plddt_md5(plddt_ch, md5_combined_ch)

    // =========================================
    // PHASE 7: Final Assembly
    // =========================================

    // Transform consensus with structure data
    transformed_consensus_ch = transform_consensus(
        consensus_filtered_ch.filtered,
        md5_combined_ch,
        stride_summaries_ch.collect(),
    )

    // Generate AF domain IDs
    af_domain_ids_ch = run_AF_domain_id(transformed_consensus_ch)

    // Collect intermediate results
    intermediate_results_ch = collect_results(
        collected_chainsaw_ch,
        collected_merizo_ch,
        collected_unidoc_ch,
    )

    // Generate final comprehensive results
    final_results_ch = collect_results_final(
        transformed_consensus_ch,
        globularity_ch,
        plddt_with_md5_ch,
        taxonomy_ch,
    )

    // =========================================
    // PHASE 8: Output Generation
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
