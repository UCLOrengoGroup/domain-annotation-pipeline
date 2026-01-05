process foldseek_process_results {
    //tag "chunk_${task.index}"
    tag "chunk_${id}"
    publishDir "${params.results_dir}" , mode: 'copy'

    input:
    //path m8_file
    tuple val(id), path(m8_file)
    each path(lookup_file)
    each path(parser_script)

    output:
    //path "foldseek_parsed_results_${task.index}.tsv", emit: foldseek_parsed_results
    tuple val(id), path("foldseek_parsed_results.tsv"), emit: foldseek_parsed_results

    script:
    //python3 ${parser_script} -i ${m8_file} -c ${lookup_file} -o foldseek_parsed_results_${task.index}.tsv
    """
    python3 ${parser_script} -i ${m8_file} -c ${lookup_file} -o foldseek_parsed_results.tsv
    """
}