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
// include { collect_taxonomy } from '../modules/collect_taxonomy.nf'
// include { extract_pdb_from_zip } from '../modules/extract_pdb_from_zip.nf'
include { filter_pdb_from_zip } from '../modules/filter_pdb_from_zip.nf'
// New process to create and transform an input mapping (id and zip) into chunk files within zips
include { create_input_from_zip } from '../modules/create_input_from_zip.nf'
include { chunk_ids_by_zip as chunk_by_zip        } from '../modules/chunk_by_zipfile.nf'
include { chunk_ids_by_zip as heavy_chunk_by_zip  } from '../modules/chunk_by_zipfile.nf'
include { light_chunk_consensus_by_zip } from '../modules/light_chunk_consensus_by_zipfile.nf'
// Domain prediction modules
include { run_ted_segmentation } from '../modules/run_ted_segmentation.nf'

// Filtering and consensus modules - these are all unused as ted_segmentation takes care of all of this funtionality.
//include { run_filter_domains } from '../modules/run_filter_domains.nf'
//include { run_filter_domains_reformatted as run_filter_domains_reformatted_unidoc } from '../modules/run_filter_domains_reformatted.nf'
//include { run_filter_domains_reformatted as run_filter_domains_reformatted_merizo } from '../modules/run_filter_domains_reformatted.nf'
//include { convert_merizo_results } from '../modules/convert_merizo_results.nf'
//include { convert_unidoc_results } from '../modules/convert_unidoc_results.nf'
//include { run_get_consensus } from '../modules/run_get_consensus.nf'
//include { run_filter_consensus } from '../modules/run_filter_consensus.nf'

// Post-processing modules
//include { chop_pdb } from '../modules/chop_pdb.nf'
include { chop_pdb_from_zip } from '../modules/chop_pdb_from_zip.nf'
include { create_md5 } from '../modules/create_domain_md5.nf'
include { run_stride } from '../modules/run_stride.nf'
//include { summarise_stride } from '../modules/summarise_stride.nf'
include { transform_consensus } from '../modules/transform.nf'

// Analysis modules
include { run_domain_quality } from '../modules/run_domain_quality.nf'
include { run_measure_globularity } from '../modules/run_measure_globularity.nf'
include { run_plddt } from '../modules/run_plddt.nf'
include { join_plddt_md5 } from '../modules/join_plddt_md5.nf'

// Final collection modules
include { collect_results } from '../modules/collect_results_combine_chopping.nf'
include { collect_results_final } from '../modules/collect_results_add_metadata.nf'
//include { run_AF_domain_id } from '../modules/run_create_AF_domain_id.nf'

// Foldseek modules
include { fetch_foldseek_assets } from '../foldseek/modules/foldseek_fetch_foldseek_assets.nf'
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

    if (!params.chunk_size || (params.chunk_size as Integer) <= 0 ) {
        error("Chunk size must be a positive integer.")
    }

    if (params.debug && !params.max_entries) {
        params.max_entries = 10
    }

    if (!params.input_zip_dir) {
        error("--input_zip_dir must be specified.")
    }

    // Ensure results directory exists
    if (!file(params.results_dir).exists()) {
        file(params.results_dir).mkdirs()
    }

    // Validate required parameters
    if (!params.input_zip_dir || !file(params.input_zip_dir).exists()) {
        error("Input ZIP directory not found: ${params.input_zip_dir}")
    }
    // Validate optional uniprot_tsv_file format (first 100 lines)
    if (params.uniprot_tsv_file) {
        def mappingFile = file(params.uniprot_tsv_file)
        if (!mappingFile.exists()) {
            error("UniProt TSV file not found: ${params.uniprot_tsv_file}")
        }
        mappingFile.readLines().take(100).eachWithIndex { line, idx ->
            def cols = line.split('\t')
            if (cols.size() != 2)
                error("Invalid TSV mapping: line ${idx + 1} does not have 2 tab-separated columns")
            if (!cols[1].endsWith('.zip'))
                error("Invalid TSV mapping: line ${idx + 1} zip name must end with .zip")
        }
    }
    // Foldseek asset existence check
    def db_exists     = params.target_db   && file(params.target_db).exists() // Check existence of target_db
    def lookup_exists = params.lookup_file && file(params.lookup_file).exists() // Check existence of lookup_file
    params.fetch_foldseek_assets = !(db_exists && lookup_exists) // Decide whether assets must be fetched

    // Foldseek-specific validation
    if (!params.parser_script || !file(params.parser_script).exists()) {
        error("Foldseek parser_script not found: ${params.parser_script}")
    }
    log.info(
        """
    ==============================================
    Domain Annotation Pipeline
    ==============================================
    Project name        : ${params.project_name}
    UniProt TSV file    : ${params.uniprot_tsv_file ?: 'N/A'}
    Input ZIP folder    : ${params.input_zip_dir}
    Main chunk size     : ${params.chunk_size}
    Light chunk size    : ${params.light_chunk_size}
    Heavy chunk size    : ${params.heavy_chunk_size}
    Min chain residues  : ${params.min_chain_residues}
    Max entries (debug) : ${params.max_entries ?: 'N/A'}
    Results dir         : ${params.results_dir}
    Debug mode          : ${params.debug}
    ----------------------------------------------
    Foldseek Configuration Information
    ----------------------------------------------
    Target database     : ${params.foldseek_db_url.tokenize('/')[-1]}
    Lookup file         : ${params.foldseek_lookup_url.tokenize('/')[-1]}
    Foldseek assests dir: .../${params.cache_dir.tokenize('/')[-3]}/${params.cache_dir.tokenize('/')[-2]}/${params.cache_dir.tokenize('/')[-1]}
    Assets status       : ${params.fetch_foldseek_assets ? 'Fetching new assets' : 'Using existing assets'}
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
    // PHASE 0: Setup Foldseek Assets
    // =========================================
    if (params.auto_fetch_foldseek_assets) {
        // Download foldseek assets: storeDir + fetch_foldseek_assets checks for missing files or change in URL and downloads if required
        fetch_foldseek_assets()
        // Use process outputs - Nextflow ensures fetch completes before downstream processes start
        ch_target_db = fetch_foldseek_assets.out.target_db
        ch_lookup_file = fetch_foldseek_assets.out.lookup_file

    } else {
        // Manual mode - specifies custom CATH database file locations
        // Usage: set --auto_fetch_foldseek_assets to false and --target_db /path/to/db --lookup_file /path/to/lookup
        if (!file(params.target_db).exists()) {
            error("Foldseek target_db file not found: ${params.target_db}")
        }
        if (!file(params.lookup_file).exists()) {
            error("Foldseek lookup_file not found: ${params.lookup_file}")
        }
        ch_target_db = Channel.value(file(params.target_db))
        ch_lookup_file = Channel.value(file(params.lookup_file))
    }

    // =========================================
    // PHASE 1: Data Preparation
    // =========================================

    // Create a subfolder in the results directory for the light_chunk_size debugging files
    file("${params.results_dir}/consensus_chunks").mkdirs()
    
    // A TSV file (two columns: id <TAB> zip_name) may be specified at runtime with param --uniprot_tsv_file to list ids and zip names.
    if (params.uniprot_tsv_file) {
        input_mapping_ch = Channel.fromPath(params.uniprot_tsv_file, checkIfExists: true)
    } else {
    // If not, create the ids and zip file channel directly from the zips in --input_zip_dir (mandatory runtime input).
        input_mapping_ch = create_input_from_zip(file(params.input_zip_dir), file(params.create_input_from_zip_script))
    }
    // zip_id_ch splits the mapping file into [id, zip_name] tuples for downstream processing
    zip_id_ch = input_mapping_ch                                    // Create a channel from the input
        .splitCsv(sep: '\t')                                        // Split into individual values by row
        .map { row -> tuple(row[0].trim(), row[1].trim()) }         // Assign the id from col 1 and the zip file from col 2
        .filter { id, zip_name -> id != '' && zip_name != '' }      // Filter blank id rows
        .unique()                                                   // Remove duplicates
        .toSortedList { a, b -> a[0] <=> b[0] }                     // Sort by id for deterministic order
        .flatMap { it }                                             // Flatten into a list to stream into the channel
    // Resultant zip_id_ch is [id, zip_name]
    
    // Apply debug limit if enabled
    if (params.debug && params.max_entries) {
        zip_id_ch = zip_id_ch.take(params.max_entries)
    }

    // Now create a file called all_ids_mapping.txt which contains two columns: [id, zip_name].
    all_ids_mapping_ch = zip_id_ch
        .map { id, zip -> "${id}\t${zip}" }
        .collectFile(
            name: 'all_ids_mapping.txt',
            newLine: true,
            sort: true,
            storeDir: "${params.results_dir}/intermediate"
        )
    
    // chunk_ids_by_zip splits all_ids_mapping.txt into chunk_size chunks within zips, assigning a 3-part tuple [chunk_id, chunk_file, zip_name].
    zip_chunks = chunk_by_zip(all_ids_mapping_ch, params.chunk_size, file(params.chunk_by_zip_script))

    // Recreate the original chunked_ids_mapping_ch from the 3-part tuple output of chunk_by_zip. This feeds filter_pdb_from_zip.
    chunked_ids_mapping_ch = zip_chunks.chunk_mapping
    .splitCsv(header: true, sep: '\t')
    .map { row ->
        tuple(
            row.chunk_id as int,
            file(row.chunk_file),
            file("${params.input_zip_dir}/${row.zip_name}")
        )
    }
    // As a branch channel, create a 2-part tuple channel [chunk_id, chunk_file] just for get_uniprot_data
    chunked_tax_ids_ch = chunked_ids_mapping_ch
        .map { chunk_id, id_file, zip_name ->
        tuple(chunk_id, id_file) }

    // Get taxonomic data using the new chunked_tax_ids_ch which only has [chunk_id, chunk_file]
    uniprot_data_ch = get_uniprot_data(chunked_tax_ids_ch)
    collected_taxonomy_ch = uniprot_data_ch
        .toSortedList { it -> it[0] }
        .flatMap{ it }
        .collectFile(
            name: 'all_taxonomy.tsv',
            keepHeader: true,
            skip: 1,
            sort: false,
            storeDir: params.results_dir,
        ) { it[1] }
    
    // Determine which ZIP archive downstream should use.
    // If cif_mode is enabled, first convert the input CIF.GZ ZIP to a PDB ZIP. If not continue with PDB ZIP file.
    // For the multizip (sharded) input - this block becomes redundant. Remove input_zip_ch and pdb_zip_ch. 
    //input_zip_ch = Channel.value(file(params.pdb_zip_file))

    //if (params.cif_mode) {
    //    pdb_zip_ch = prepare_pdb_file(input_zip_ch)
    //} else {
    //    pdb_zip_ch = input_zip_ch
    //}
    // Run filter_pdb_from_zip on the 3-part tuple chunked data channel (creates filtered lists) - removed pdb_zip_ch.
    filtered_ids_ch = filter_pdb_from_zip(chunked_ids_mapping_ch, params.min_chain_residues)
    
    // =========================================
    // PHASE 2: Domain Prediction
    // =========================================

    // Rechunk for ted_segmentation using heavy_chunk_size. First, take the filtered output and return to 2-part tuple [chunk_id <tab> zip_name]
    filtered_two_part_ch = filtered_ids_ch
        .flatMap { chunk_id, filtered_file, zip_name ->
            filtered_file.text
                .readLines()
                .findAll { it.trim() }
                .collect { id -> "${id.trim()}\t${zip_name}" }
        }
        .collectFile(
            name: 'filtered_af_ids.txt', // Write the chunks to an output file
            newLine: true,
            sort: true,
            storeDir: "${params.results_dir}/intermediate"
        )

    // Use process chunk_ids_by_zip to split filtered_af_ids.txt into heavy_chunk_size chunks within zips, assigning the 3-part tuple [chunk_id, chunk_file, zip_name].
    heavy_chunks = heavy_chunk_by_zip(filtered_two_part_ch, params.heavy_chunk_size, file(params.chunk_by_zip_script))
    
    // Create heavy_chunk_ch as a channel from the process output
    heavy_chunk_ch = heavy_chunks.chunk_mapping
    .splitCsv(header: true, sep: '\t')
    .map { row ->
        tuple(row.chunk_id as int, file(row.chunk_file), file("${params.input_zip_dir}/${row.zip_name}"))
    }
    
    // Finally run the ted_segmentation which now includes the extract from zip code. Again removed pdb_zip_ch.
    segmentation_ch = run_ted_segmentation(heavy_chunk_ch)

    // =========================================
    // PHASE 3: Results Collection & Filtering
    // =========================================

    // collect the results for chainsaw, merizo and unidoc output - now added sorting to each to help cache performance.
    collected_chainsaw_ch = segmentation_ch.chainsaw
        .toSortedList { it -> it[0] }
        .flatMap { it }
        .collectFile(
            name: 'domain_assignments.chainsaw.tsv',
            sort: false,
            storeDir: params.results_dir,
        ) { it[1] }

    collected_merizo_ch = segmentation_ch.merizo
        .toSortedList { it -> it[0] }
        .flatMap { it }
        .collectFile(
            name: 'domain_assignments.merizo.tsv',
            sort: false,
            storeDir: params.results_dir,
        ) { it[1] }

    collected_unidoc_ch = segmentation_ch.unidoc
        .toSortedList { it -> it[0] }
        .flatMap { it }
        .collectFile(
            name: 'domain_assignments.unidoc.tsv',
            sort: false,
            storeDir: params.results_dir,
        ) { it[1] }

    // collect the results for the consensus output - note: this channel drives the rest of the workflow.
    // TODO: current behaviour (storeDir) writes to a permanent file in results. Enhancement: update to use a cached work directory.
    collected_consensus_ch = segmentation_ch.consensus
        .toSortedList { it -> it[0] }
        .flatMap { it }
        .collectFile(
            name: 'domain_assignments.consensus.tsv',
            sort: false,
            storeDir: params.results_dir,
        ) { it[1] }

    // =========================================
    // PHASE 4: Post-Consensus Processing
    // =========================================
    // TODO: chunks are written from the storeDir file created above. Changes may not be reflected in the consensus_chunks.
    // Accidental deletion of the consensus_chunks directory will result in pipeline failure.
    // Reassign light_chunk_size channel for lighter downstream processes using [consensus_file, zip_name]
    consensus_chunks_ch = segmentation_ch.consensus
        .toSortedList { it -> it[0] }
        .flatMap { it }
        .flatMap { chunk_id, consensus_file, zip_name ->
            consensus_file.text
                .readLines()
                .findAll { it.trim() }
                .collect { row -> "${row}\t${zip_name}" }
        }
    .collectFile(
        name: 'consensus_with_zip.tsv',
        newLine: true,
        sort: false,
        //storeDir: "${params.results_dir}/consensus_chunks"
    )
    // Call the process to make sure this file is chunked within zip.
    light_chunks = light_chunk_consensus_by_zip(consensus_chunks_ch, params.light_chunk_size, file(params.light_chunk_consensus_by_zip_script))
    
    // Create light_chunk_ch as a channel from light_chunk_consensus_by_zip output
    light_chunk_ch = light_chunks.light_chunk_mapping
    .splitCsv(header: true, sep: '\t')
    .map { row ->
        tuple(row.chunk_id, file(row.chunk_file), file("${params.input_zip_dir}/${row.zip_name}"))
    }

    // Chop pdbs in parallel using chunks and extracting from zip on-the-fly. Removed pdb_zip_ch and replaced with the 3-part tuple
    chopped_pdb_ch = chop_pdb_from_zip(light_chunk_ch)
        
    // Generate MD5 hashes for domains added a new file and script_ch - NEW CODE
    md5_chunks_ch = create_md5(chopped_pdb_ch)
    collected_md5_ch = md5_chunks_ch
        .toSortedList { it -> it[0] }
        .flatMap{ it }
        .collectFile(
            name: "all_md5.tsv",
            keepHeader: true,
            skip: 1,
            sort: false,
            storeDir: params.results_dir,
        ) { it[1] }

    // =========================================
    // PHASE 5: Structure Analysis
    // =========================================

    // Run STRIDE analysis
    stride_summary_script_ch = file(
        "${workflow.projectDir}/../docker/script/create_stride_summary.py", // this becomes input:stride_summary_script
        checkIfExists: true)
    
    stride_summaries_ch = run_stride(chopped_pdb_ch, stride_summary_script_ch)

    collected_stride_summaries_ch = stride_summaries_ch
        .toSortedList { it -> it[0] }
        .flatMap{ it }
        .collectFile(
            name: "all_stride_summaries.tsv",
            keepHeader: true,
            skip: 1,
            sort: false,
            storeDir: params.results_dir,
        ) { it[1] } // use file name to collect
    
    // Run globularity analysis
    globularity_ch = run_measure_globularity(chopped_pdb_ch)
    // globularity_ch.view { "globularity_ch: " + it }
    // no flatten as only a single file per chunk
    collected_globularity_ch = globularity_ch
        .toSortedList { it -> it[0] }
        .flatMap{ it }
        .collectFile(
            name: "all_domain_globularity.tsv",
            keepHeader: true,
            skip: 1,
            sort: false,
            storeDir: params.results_dir,            
        ) { it[1] } // use file name to collect

    // Run domain quality
    domain_quality_ch = run_domain_quality(chopped_pdb_ch)

    collected_domain_quality_ch = domain_quality_ch
        .toSortedList { it -> it[0] }
        .flatMap{ it }
        .collectFile(
            name: "all_domain_quality.csv",
            keepHeader: true,
            skip: 1,
            sort: false,
            storeDir: params.results_dir,
        ) { it[1] } // use file name to collect

    // Run pLDDT analysis
    plddt_ch = run_plddt(chopped_pdb_ch)
    // plddt_ch.view { "plddt_ch: " + it }
    // no flatten as only a single file per chunk
    collected_plddt_ch = plddt_ch
        .toSortedList { it -> it[0] }
        .flatMap{ it }
        .collectFile(
            name: "all_plddt.tsv",
            sort: false,
            storeDir: params.results_dir,
        ) { it[1] } // use file name to collect

    collected_plddt_with_md5_ch = join_plddt_md5(collected_plddt_ch, collected_md5_ch)

    // =========================================
    // PHASE 6: Run foldseek
    // =========================================

    // Create the query DB from the chopped pdbs channel
    foldseek_create_db(chopped_pdb_ch) // New - run stright off chopped_pdb chunked output

    // Run foldseek search on the output of process create_foldseek_db and the CATH database
    fs_search_ch = foldseek_run_foldseek(foldseek_create_db.out.query_db_dir, ch_target_db)
    
    // Convert results with fs convertalis, pass query_db, CATH_db and output db from run_foldseek
    fs_m8_ch = foldseek_run_convertalis(fs_search_ch, ch_target_db)

    // Parse output - first create a channel from the location of the python and look_up scripts
    ch_parser_script = Channel.value(file(params.parser_script))
    //ch_parser_script = Channel.fromPath(params.parser_script, checkIfExists: true)
    
    // Now pass the convertalis .m8 and python script as intputs to the parsing process
    fs_parsed_ch = foldseek_process_results(fs_m8_ch, ch_lookup_file, ch_parser_script)
    
    // Finally combine results together with a similar collectFile statement as used above
    foldseek_ch = fs_parsed_ch
        .toSortedList { it -> it[0] }
        .flatMap{ it }
        .collectFile( 
            name: 'foldseek_parsed_results.tsv',
            keepHeader: true,
            skip: 1,
            sort: false,
            storeDir: params.results_dir,
        ) { it[1] }

    // =========================================
    // PHASE 7: Final Assembly
    // =========================================

    // Transform consensus with structure data
    transformed_consensus_ch = transform_consensus(
        collected_consensus_ch,
        collected_md5_ch,
        collected_stride_summaries_ch,
    )

    // Collect intermediate results
    intermediate_results_ch = collect_results(
        collected_chainsaw_ch,
        collected_merizo_ch,
        collected_unidoc_ch,    
    )

    // This hard codes combine_results_final.py as the input to the collect_results_final process. 
    collect_results_script_ch = Channel.fromPath(
        "${workflow.projectDir}/../docker/script/combine_results_final.py", // this becomes input:combine_script
        checkIfExists: true
    )
    // Now collect the final results
    final_results_ch = collect_results_final(
        collect_results_script_ch,
        transformed_consensus_ch,
        collected_globularity_ch,
        collected_plddt_with_md5_ch,
        collected_domain_quality_ch,
        collected_taxonomy_ch,
        foldseek_ch,
    )

    // ==========================================
    // PHASE 8: Completion and output Information
    // ==========================================

    // Remove duplicate final output file and log the location of final_results.tsv to screen
    final_results_ch
        .map { def output_path = "${params.results_dir}/final_results.tsv"
            log.info("Final results written to: ${output_path}")
            return output_path
        }

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
