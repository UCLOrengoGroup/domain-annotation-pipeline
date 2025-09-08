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
params.base_code_dir = '/SAN/orengolab/bfvd/code'
params.run_quality_checks_script = "${params.base_code_dir}/domain-annotation-pipeline/docker/scripts/run_quality_checks.py"
params.chopped_pdb_dir = "${params.base_code_dir}/2025_09_03.post_processing/example_pdbs"
params.dom_path = "${params.base_code_dir}/dom/dom"
params.dom_qual_path = "${params.base_code_dir}/domqual/pytorch_foldclass_pred_dir.py"
params.chunk_size = 100

def validateParameters() {
    if (!file(params.chopped_pdb_dir).exists()) {
        error "Chopped PDB directory does not exist: ${params.chopped_pdb_dir}"
    }
    if (!file(params.dom_path).exists()) {
        error "Domain path does not exist: ${params.dom_path}"
    }
    if (!file(params.dom_qual_path).exists()) {
        error "Domain quality path does not exist: ${params.dom_qual_path}"
    }
    log.info(
        """
    ==============================================
    Postprocess Pipeline
    ==============================================
    Project name        : ${params.project_name}
    PDB dir             : ${params.chopped_pdb_dir}
    Main chunk size     : ${params.chunk_size}
    Work dir            : ${params.work_dir}
    Results dir         : ${params.results_dir}
    Debug mode          : ${params.debug}
    ==============================================
    """.stripIndent()
    )
}

process run_quality_checks {

    input:
    path "pdb/*.pdb"

    output:
    path "quality.csv"

    script:
    """
    python3 ${params.run_quality_checks_script} -d pdb/ -o quality.csv --dom-path ${params.dom_path} --dom-qual-path ${params.dom_qual_path}
    """
}

// ===============================================
// MAIN WORKFLOW
// ===============================================

workflow {

    validateParameters()

    // get PDBs from chopped PDB directory
    // chunk into chunk_size
    chopped_pdb_ch = Channel.fromPath("${params.chopped_pdb_dir}/*.pdb")
        .buffer(size: params.chunk_size, remainder: true)

    quality_results_ch = run_quality_checks(chopped_pdb_ch)
    quality_summary_ch = quality_results_ch.flatten().collect()

    quality_summary_ch.view()
}
