process foldseek_process_results {
    label 'sge_low'
    container 'domain-annotation-pipeline-script' 
    //publishDir "${params.results_dir}" , mode: 'copy' // unnecessary as it is already covered in collectFile 

    input:
    tuple val(id), path(m8_file)
    path(lookup_file)
    path(parser_script)

    output:
    tuple val(id), path("foldseek_parsed_results.tsv"), emit: foldseek_parsed_results

    script:
    """
    python3 ${parser_script} -i ${m8_file} -c ${lookup_file} -o foldseek_parsed_results.unsorted.tsv
    if [ ! -s foldseek_parsed_results.unsorted.tsv ]; then
        printf "query_id\ttarget_id\tevalue\ttmscore\tcode\ttype\tqcov\ttcov\nNA\tNA\tNA\tNA\tNA\tNA\tNA\tNA\n" > foldseek_parsed_results.tsv
    else
        head -n 1 foldseek_parsed_results.unsorted.tsv > foldseek_parsed_results.tsv
        tail -n +2 foldseek_parsed_results.unsorted.tsv | sort >> foldseek_parsed_results.tsv
    fi
    """
}