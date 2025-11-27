/*
 * Collect the 3 filtered FILENAMES from filter_domains.py, save them into a csv file as a check and pass names onto runGetConsensus.
 */
process collect_chopping_names {
    label 'sge_low'
    publishDir "${params.results_dir}"
    
    input:
        path filtered_file

    output:
        path "collected_output.csv"

    script:
    """
    echo "${filtered_file.name}" > collected_output.csv
    """
}