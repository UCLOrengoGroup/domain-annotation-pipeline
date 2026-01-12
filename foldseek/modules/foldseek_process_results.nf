process foldseek_process_results {
    publishDir "${params.results_dir}" , mode: 'copy'

    input:
    tuple val(id), path(m8_file)
    each path(lookup_file)
    each path(parser_script)

    output:
    tuple val(id), path("foldseek_parsed_results.tsv"), emit: foldseek_parsed_results

    script:
    """
    python3 ${parser_script} -i ${m8_file} -c ${lookup_file} -o foldseek_parsed_results.tsv
    """
}