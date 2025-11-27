/*
 * Run filter_domains.py on the 3 output files (domain_assignments.merizo.tsv, domain_assignments.chaninsaw.tsv' and domain_assignments.unidoc.tsv).
 * command format is changed from: python filter_domains.py <chopping_file> -o filtered_<chopping_file>.txt to create 3 filtered output files.
 * to: 
 */
process run_filter_domains {
    label 'sge_low'
    container 'domain-annotation-pipeline-ted-tools'
    publishDir "${params.results_dir}" , mode: 'copy'

    input:
        path chopping_file

    output:
        path "filtered_${chopping_file.name}"

    script:
    """
    ${params.prefilter_script} ${chopping_file} -o filtered_${chopping_file.name}
    """
}