process collect_taxonomy {
    label 'sge_low'
    publishDir "${params.results_dir}" , mode: 'copy'

    input:
        path input_files

    output:
        path "all_taxonomy.tsv", emit: output_file

    script:
    """
    cat ${input_files} > 'all_taxonomy.tsv'
    """
}
