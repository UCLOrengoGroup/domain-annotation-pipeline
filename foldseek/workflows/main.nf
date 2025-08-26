#!/usr/bin/env nextflow
//params.chunk_size = 3
nextflow.enable.dsl=2

// a list of all the processes
//include { filter_domain_agreement } from '../modules/filter_domain_agreement,nf'
include { create_db }               from '../modules/create_foldseek_db.nf'
include { run_foldseek }            from '../modules/run_foldseek.nf'
include { run_convertalis }         from '../modules/run_convertalis.nf'
include { parse_foldseek }          from '../modules/process_foldseek.nf'

// the workflow
workflow {
    // Create the query DB from the folder containing chopped pdb (see config file)
    ch_pdbs = Channel.fromPath("${params.pdbs_dir}/*.pdb")
                    .buffer(size: params.chunk_size, remainder: true)
    create_db(ch_pdbs)

    // Define the target (CATH) database using config: params.target_db
    ch_target_db = Channel.fromPath(params.target_db)
    // Run foldseek search on the output of process create_foldseek_db and the CATH database
    run_foldseek(create_db.out.query_db_dir, ch_target_db)

    // Convert results with fs convertalis, pass query_db, CATH_db and output db from run_foldseek
    run_convertalis(create_db.out.query_db_dir, ch_target_db, run_foldseek.out.result_db_dir)

    // Parse output - first create a channel from the location of the python script
    ch_parser_script = Channel.fromPath(params.parser_script, checkIfExists: true)
    // Now pass the convertalis .m8 and the python script as intput to the parsing process
    parse_foldseek(run_convertalis.out.m8_output, ch_parser_script)
}