#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

/*
 * Homcheck - Main Workflow
 * 
 * This workflow processes chopped PDBs from the domain-annotation-pipeline and generates homology hits to CATH
 * via FoldSeek, constrasTED and Foldclass (Merizo-search). 
 * It requres a directory of tar.gz files contating the chopped PDBs and a tsv of matching sequence data.
 */

// ===============================================
// PARAMETERS
// ===============================================
// Output directory
params.results_dir = params.results_dir ?: "${workflow.launchDir}/results/${params.project_name}"
params.publish_mode = 'copy'

// ===============================================
// MODULE IMPORTS
// ===============================================
// Data preparation modules
include { chunk_md5 } from '../modules/chunk_md5.nf'

// Foldseek modules
include { fetch_foldseek_assets } from '../foldseek/modules/foldseek_fetch_foldseek_assets.nf'
include { foldseek_create_db } from '../foldseek/modules/foldseek_create_db.nf'
include { foldseek_run_foldseek } from '../foldseek/modules/foldseek_run_foldseek.nf'
include { foldseek_run_convertalis } from '../foldseek/modules/foldseek_run_convertalis.nf'
include { foldseek_process_results } from '../foldseek/modules/foldseek_process_results.nf'

// contrasTED modules
include { fetch_contrasted_assets } from '../modules/contrasted_fetch_db_assets.nf'
include { contrasted_run_annotate } from '../modules/contrasted_run_annotate.nf'

// FoldClass modules
include { fetch_foldclass_assets } from '../modules/foldclass_fetch_db_assets.nf'
include { foldclass_run_dbsearch } from '../modules/foldclass_dbsearch.nf'
// ===============================================
// HELPER FUNCTIONS
// ===============================================
def warnOnArchitectureMismatch() {
    def jvmArch = (System.getProperty('os.arch') ?: 'unknown').toLowerCase()
    def hostArch = 'unknown'

    try {hostArch = 'uname -m'.execute().text.trim().toLowerCase()
    } catch (Exception _ignored) {}

    def hostIsArm = hostArch.contains('aarch64') || hostArch.contains('arm64')
    def jvmIsX86 = jvmArch.contains('x86_64') || jvmArch.contains('amd64')

    if (hostIsArm && jvmIsX86) {log.warn(
            """
            =====================================================================
            Architecture mismatch detected
            ---------------------------------------------------------------------
            Host architecture          : ${hostArch}
            JVM architecture           : ${jvmArch}
            Resolved container tag     : ${params.container_tag_name}

            This often causes amd64 container selection on arm64 hosts and slower
            emulated execution (notably in run_ted_segmentation).

            Recommended actions:
            - Use an arm64 JDK so Java reports arm64/aarch64
            - Or override tags explicitly: --container_tag_name <existing-tag>
            =====================================================================
            """.stripIndent()
        )
    }
}

def validateParameters() {

    warnOnArchitectureMismatch()
    // Validate parameters
    if (!params.project_name) {error("Project name must be specified in the parameters.")}
    if (!params.pdb_tar_dir) {error("--pdb_tar_dir must be specified.")}
    if (!params.md5_file) {error("--md5_file must be specified.")}

    // Ensure directories and parameter files exists
    if (!file(params.results_dir).exists()) {file(params.results_dir).mkdirs()}
    if (!file(params.reports_dir).exists()) {file(params.reports_dir).mkdirs()}
    if (!params.pdb_tar_dir || !file(params.pdb_tar_dir).exists()) {error("Input tar directory not found: ${params.pdb_tar_dir}")}
    if (!params.md5_file || !file(params.md5_file).exists()) {error("md5 file not found: ${params.md5_file}")}

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
    Homcheck Pipeline
    ==============================================
    Project name        : ${params.project_name}
    Chopped PDB folder  : ${params.pdb_tar_dir}
    MD5 file used       : ${params.md5_file}
    Results dir         : ${params.results_dir}
    Reports dir         : ${params.reports_dir}
    Debug mode          : ${params.debug}
    ----------------------------------------------
    Foldseek Configuration Information
    ----------------------------------------------
    Target database     : ${params.foldseek_db_url.tokenize('/')[-1]}
    Lookup file         : ${params.foldseek_lookup_url.tokenize('/')[-1]}
    Foldseek assests dir: .../${params.cache_dir.tokenize('/')[-3]}/${params.cache_dir.tokenize('/')[-2]}/${params.cache_dir.tokenize('/')[-1]}
    Assets status       : ${params.fetch_foldseek_assets ? 'Fetching new assets' : 'Using existing assets'}
    ----------------------------------------------
    contrasTED Configuration Information
    ----------------------------------------------
    Reference database  : ${params.contrasted_db_url.tokenize('/')[-1]}
    ProstT5 location    : ${params.contrasted_hf_home}
    ----------------------------------------------
    Foldclass Configuration Information
    ----------------------------------------------
    Reference database  : ${params.foldclass_db_url.tokenize('/')[-1]}
    Foldclass assets dir: .../${params.foldclass_db_dir.tokenize('/')[-3]}/${params.foldclass_db_dir.tokenize('/')[-2]}/${params.foldclass_db_dir.tokenize('/')[-1]}
    ==============================================
    """.stripIndent()
    )
}

// ===============================================
// MAIN WORKFLOW
// ===============================================
workflow {
    
    validateParameters()
    
    // =============================================
    // PHASE 1: Setup Foldseek Assets
    // =============================================

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
        ch_target_db   = channel.value(file(params.target_db))
        ch_lookup_file = channel.value(file(params.lookup_file))
    }

    // =============================================
    // PHASE 2: Setup contrasTED Assets
    // =============================================

    if (params.auto_fetch_contrasted_assets) {
        fetch_contrasted_assets()
        contrasted_db_ch   = fetch_contrasted_assets.out.reference_db
        contrasted_list_ch = fetch_contrasted_assets.out.domain_list
    } else {
        if (!file(params.contrasted_db_path).exists()) {
            error("Contrasted database file not found: ${params.contrasted_db_path}")
        }
        if (!file(params.contrasted_list_path).exists()) {
            error("Contrasted domain list file not found: ${params.contrasted_list_path}")
        }
        contrasted_db_ch   = channel.value(file(params.contrasted_db_path))
        contrasted_list_ch = channel.value(file(params.contrasted_list_path))
    }

    // =============================================
    // PHASE 3: Setup FoldClass Assets
    // =============================================

    if (params.auto_fetch_foldclass_assets) {
        fetch_foldclass_assets()
        foldclass_db_ch      = fetch_foldclass_assets.out.reference_db
        foldclass_targets_ch = fetch_foldclass_assets.out.targets_list
    } else {
        if (!file(params.foldclass_db).exists()) {
            error("Foldclass pt file not found: ${params.foldclass_db}")
        }
        if (!file(params.foldclass_targets).exists()) {
            error("Foldclass targets file not found: ${params.foldclass_targets}")
        }
        foldclass_db_ch = channel.value(file(params.foldclass_db))
        foldclass_targets_ch = channel.value(file(params.foldclass_targets))
    }

    // =========================================
    // PHASE 4: Data Preparation and inputs
    // =========================================
    // Create [chunk_id, chopped_pdb_tar] tuples from the chopped PDB tar files
    chopped_pdb_ch = Channel
        .fromPath("${params.pdb_tar_dir}/*.tar.gz", checkIfExists: true)
        .map { tar_file ->
            def chunk_id = tar_file.name.replaceFirst(/\.tar\.gz$/, '')
            tuple(chunk_id, tar_file)}
    
    // Create contrasTED input: split all_md5.tsv into manageable chunks: [chunk_id, md5_chunk_file]
    md5_file_ch = Channel.fromPath(params.md5_file, checkIfExists: true)

    chunk_md5(md5_file_ch, params.contrasted_chunk_size)

    md5_chunks_ch = chunk_md5.out.chunks
        .flatten()
        .map { md5_file ->
            def chunk_id = md5_file.baseName.replaceFirst(/^md5_chunk_/, '')
            tuple(chunk_id, md5_file)
        }
    // =========================================
    // PHASE 5: Run Foldseek
    // =========================================

    // Create the query DB from the chopped pdbs channel
    foldseek_create_db(chopped_pdb_ch) // New - run stright off chopped_pdb chunked output

    // Run foldseek search on the output of process create_foldseek_db and the CATH database
    fs_search_ch = foldseek_run_foldseek(foldseek_create_db.out.query_db_dir, ch_target_db)
    
    // Convert results with fs convertalis, pass query_db, CATH_db and output db from run_foldseek
    fs_m8_ch = foldseek_run_convertalis(fs_search_ch, ch_target_db)

    // Parse output - first create a channel from the location of the python and look_up scripts
    ch_parser_script = channel.value(file(params.parser_script))
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
    // PHASE 6: Run contrasTED
    // =========================================
    // Run contrasted-annotate from the all_md5 file.
    contrast_ch = contrasted_run_annotate(md5_chunks_ch, contrasted_db_ch, contrasted_list_ch)
    
    // Combine results from each chunk together
    cont_collect_ch = contrast_ch
        .toSortedList { it -> it[0] }
        .flatMap{ it }
        .collectFile( 
            name: 'contrasted_results.tsv',
            keepHeader: true,
            skip: 1,
            sort: false,
            storeDir: params.results_dir,
        ) { it[1] }
    
    // ==========================================
    // PHASE 7: Run Foldclass
    // ==========================================
    // Run foldclass from the chopped_pdb channel
    foldclass_ch = foldclass_run_dbsearch(chopped_pdb_ch, foldclass_db_ch, foldclass_targets_ch)
     
    // Combine results from each chunk together
    foldclass_out_ch = foldclass_ch
        .toSortedList { it -> it[0] }
        .flatMap{ it }
        .collectFile( 
            name: 'foldclass_results.tsv',
            sort: false,
            storeDir: params.results_dir,
        ) { it[1] }

}
