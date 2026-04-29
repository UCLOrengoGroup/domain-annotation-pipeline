#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

/*
 * Prepare data for workflows/annotate.nf from AlphaFold DB IDs.
 *
 * This workflow downloads each BinaryCIF file directly from:
 *   https://alphafold.ebi.ac.uk/files/<AF_ID>.bcif
 *
 * Inputs:
 *   --af_ids_file (required) : list of AFDB IDs (one per line), e.g. AF-O15552-F1-model_v6
 *   --bcif_zip_file (optional): if provided, skip downloads and use this zip instead
 *   --af_base_url (optional)  : default https://alphafold.ebi.ac.uk/files
 *   --prep_chunk_size (optional): number of AF IDs to process per chunk; default 100000
 *
 * Outputs (written to results/<project_name>/prepared via publishDir):
 *   - af_ids.txt
 *   - failed_ids.txt
 *   - prep_summary.txt
 *   - downloaded_ids.txt
 *   - download_log.tsv
 *
 * Chunk-scoped archive outputs are published under:
 *   results/<project_name>/prepared/chunks/
 *   - <chunk_id>.bcif_files.zip
 *   - <chunk_id>.cif_files.zip
 *   - <chunk_id>.pdb_files.zip
 */

// ===============================================
// PARAMETERS
// ===============================================
params.results_dir = "${workflow.launchDir}/results/${params.project_name}"
if (!params.containsKey('publish_mode') || params.publish_mode == null) params.publish_mode = 'copy'

// Inputs
if (!params.containsKey('af_ids_file')) params.af_ids_file = null  // required: list of AFDB IDs (one per line)
if (!params.containsKey('bcif_zip_file')) params.bcif_zip_file = null  // optional: zip containing .bcif members
if (!params.containsKey('af_base_url') || params.af_base_url == null) params.af_base_url = 'https://alphafold.ebi.ac.uk/files'
if (!params.containsKey('prep_chunk_size') || params.prep_chunk_size == null) params.prep_chunk_size = 100000

// Script is staged into the task work dir so you can edit it without rebuilding containers
if (!params.containsKey('bcif_download_script') || params.bcif_download_script == null) params.bcif_download_script = "${baseDir}/../docker/script/download_bcif_from_ebi.py"
if (!params.containsKey('bcif_zip_converter_script') || params.bcif_zip_converter_script == null) params.bcif_zip_converter_script = "${baseDir}/../docker/script/make_pdb_zip.py"

include { normalise_af_ids; ids_from_bcif_zip; download_bcif_from_ebi; prepare_pdb_from_af_bcif } from '../modules/prepare_af_pdb_zip.nf'

workflow {

    if (!params.project_name) {
        error("Project name must be specified (use --project_name)")
    }

    if (!params.af_ids_file) {
        error("AF IDs file must be specified (use --af_ids_file)")
    }

    if (!params.prep_chunk_size || params.prep_chunk_size <= 0) {
        error("Prep chunk size must be a positive integer (use --prep_chunk_size)")
    }

    if (!file(params.af_ids_file).exists()) {
        error("AF IDs file not found: ${params.af_ids_file}")
    }

    file("${params.results_dir}/prepared").mkdirs()
    file("${params.results_dir}/prepared/chunks").mkdirs()

    af_ids_ch = normalise_af_ids(channel.value(file(params.af_ids_file)))
    converter_script_ch = channel.value(file(params.bcif_zip_converter_script))

    // Use either user-provided BCIF zip, or download from AlphaFold DB
    if (params.bcif_zip_file) {
        if (!file(params.bcif_zip_file).exists()) {
            error("BCIF zip file not found: ${params.bcif_zip_file}")
        }
        bcif_chunk_ch = channel.value(['chunk_000000', file(params.bcif_zip_file)])
        af_ids_for_conversion_ch = ids_from_bcif_zip(bcif_chunk_ch)
        prepare_input_ch = bcif_chunk_ch
            .join(af_ids_for_conversion_ch)
            .map { chunk_id, bcif_zip, af_ids_for_conversion_file -> [chunk_id, bcif_zip, af_ids_for_conversion_file] }

        prepare_pdb_from_af_bcif(prepare_input_ch, converter_script_ch)
    } else {
        chunked_af_ids_ch = af_ids_ch
            .splitText(by: params.prep_chunk_size, file: true)
            .toSortedList { chunkFile -> chunkFile.name }
            .flatMap { List chunkFiles ->
                chunkFiles.withIndex().collect { cf, idx ->
                    [String.format('chunk_%06d', idx), cf]
                }
            }

        download_script_ch = channel.value(file(params.bcif_download_script))
        downloads_ch = download_bcif_from_ebi(chunked_af_ids_ch, download_script_ch, params.af_base_url.replaceAll('/+$',''))

        prepare_input_ch = downloads_ch.map { chunk_id, bcif_zip, downloaded_ids, _failed_ids, _prep_summary, _download_log ->
            [chunk_id, bcif_zip, downloaded_ids]
        }

        prepare_pdb_from_af_bcif(prepare_input_ch, converter_script_ch)
        download_rows_ch = downloads_ch.toSortedList { row -> row[0] }

        download_rows_ch
            .flatMap { rows -> rows }
            .collectFile(
                name: 'downloaded_ids.txt',
                newLine: true,
                sort: false,
                storeDir: "${params.results_dir}/prepared",
            ) { row -> row[2] }

        download_rows_ch
            .flatMap { rows -> rows }
            .collectFile(
                name: 'failed_ids.txt',
                newLine: true,
                sort: false,
                storeDir: "${params.results_dir}/prepared",
            ) { row -> row[3] }

        download_rows_ch
            .flatMap { rows ->
                rows.collect { row -> "[${row[0]}]\n${row[4].text.trim()}\n" }
            }
            .collectFile(
                name: 'prep_summary.txt',
                newLine: true,
                sort: false,
                storeDir: "${params.results_dir}/prepared",
            )

        download_rows_ch
            .flatMap { rows -> rows }
            .collectFile(
                name: 'download_log.tsv',
                keepHeader: true,
                skip: 1,
                sort: false,
                storeDir: "${params.results_dir}/prepared",
            ) { row -> row[5] }
    }
}
