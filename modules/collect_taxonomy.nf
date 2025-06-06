process collect_taxonomy {

    publishDir 'results', mode: 'copy'

    input:
        path input_files

    output:
        path "All_taxonomy.tsv", emit: output_file

    script:
    """
    cat ${input_files} > 'All_taxonomy.tsv'
    """
}
