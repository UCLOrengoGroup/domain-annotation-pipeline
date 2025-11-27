process foldseek_process_results {
    publishDir "results/processed", mode: 'copy'

    input:
    path m8_file
    path parser_script

    output:
    path "parsed_results.txt", emit: parsed_results
    path "versions.yml", emit: versions

    script:
    """
    python3 ${parser_script} -i ${m8_file} -o parsed_results.txt
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python3 --version | sed 's/Python //')
    END_VERSIONS
    """
}