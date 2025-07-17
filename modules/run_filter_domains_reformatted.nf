/*
 * Run filter_domains.py on the 3 output files (domain_assignments.merizo.tsv, domain_assignments.chaninsaw.tsv' and domain_assignments.unidoc.tsv).
 * command format is changed from: python filter_domains.py <chopping_file> -o filtered_<chopping_file>.txt to create 3 filtered output files.
 * to: 
 */
process run_filter_domains_reformatted {
    label 'sge_low'
    container 'domain-annotation-pipeline-ted-tools'
    publishDir './results' , mode: 'copy'

    input:
        path reformatted_file_meriz
        path reformatted_file_uni

    output:
        path "filtered_${reformatted_file_meriz.name}"
        path "filtered_${reformatted_file_uni.name}"

    script:
    """
    ${params.prefilter_script} ${reformatted_file_meriz} -o filtered_${reformatted_file_meriz.name}
    ${params.prefilter_script} ${reformatted_file_uni} -o filtered_${reformatted_file_uni.name}
    """
}