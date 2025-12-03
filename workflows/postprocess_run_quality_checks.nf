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
// params.chunk_size = 10000
// params.all_chopped_pdbs_zip = "${params.results_dir}/all_chopped_pdbs.zip"
params.chunk_size = 5
params.all_chopped_pdbs_zip = "${baseDir}/../assets/bfvd/test_bfvd.zip"

include { run_domain_quality_from_zip } from '../modules/run_domain_quality_from_zip.nf'


def validateParameters() {
    if (!file(params.all_chopped_pdbs_zip).exists()) {
        error "Chopped PDB zip file does not exist: ${params.all_chopped_pdbs_zip}"
    }
    log.info(
        """
    ==============================================
    Postprocess Pipeline
    ==============================================
    Project name        : ${params.project_name}
    PDB zip file        : ${params.all_chopped_pdbs_zip}
    Main chunk size     : ${params.chunk_size}
    Work dir            : ${params.work_dir}
    Results dir         : ${params.results_dir}
    Debug mode          : ${params.debug}
    ==============================================
    """.stripIndent()
    )
}

process files_from_zip {
    label 'local'

    container 'domain-annotation-pipeline-ted-tools'

    input:
    path(pdb_zip)

    output:
    path('pdb_list.txt')

    script:
    """
    set -e
    zipinfo -1 ${pdb_zip} > pdb_list.txt
    """
}


// ===============================================
// MAIN WORKFLOW
// ===============================================

workflow {

    validateParameters()

    // get PDB zip
    // chunk into chunk_size
    chopped_pdb_zip_ch = Channel.value( file("${params.all_chopped_pdbs_zip}") )

    chopped_pdb_zip_ch = chopped_pdb_zip_ch.map { it -> println "Chopped PDB zip: ${it}"; it }

    all_files_ch = files_from_zip(chopped_pdb_zip_ch)

    // log.info "All chopped PDB filenames: ${all_files_ch.size()} files"

    chunked_files_ch = all_files_ch
        .collectFile(
            name: 'all_chopped_filenames.txt',
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

    // chunked_files_ch = chunked_files_ch.map { it -> println "Chunked IDs: ${it[0]} with ${it[1].size()} files:\n ${it[1]}"; it }

    quality_results_ch = run_domain_quality_from_zip(chunked_files_ch, chopped_pdb_zip_ch)

    // quality_results_ch = quality_results_ch.map { it -> println "Domain quality result chunk: ${it[0]} -> ${it[1]}"; it }

    collected_quality_ch = quality_results_ch.collectFile(
        name: 'postprocess_all_domain_quality.csv',
        keepHeader: true,
        skip: 1, 
        storeDir: params.results_dir,
        sort: { it -> it[0] } // sort by chunk id
    ) { it -> file(it[1]) } // use file name to collect

    collected_quality_ch.map { it -> println "Collected domain quality results: ${it}" }
}
