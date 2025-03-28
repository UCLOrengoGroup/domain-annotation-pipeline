/*
 * Run filter_domains.py on the 3 chopping output files (chopping_unidoc.txt, chopping_chainsaw.txt and chopping_merizo.txt)
 * command format: python filter_domains.py <chopping_file> -o filtered_<chopping_file>.txt to create 3 filtered output files.
 */
process runFilterDomains {

    publishDir './results' , mode: 'copy'
    input:
        path chopping_file

    output:
        path "filtered_${chopping_file.name}"

    script:
    """
    python ${workflow.projectDir}/bin/filter_domains.py ${chopping_file} -o filtered_${chopping_file.name}
    """
}