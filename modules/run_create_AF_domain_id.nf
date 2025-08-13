process run_AF_domain_id {
    label 'sge_low'
    container 'domain-annotation-pipeline-cath-af-cli'
    publishDir "${params.results_dir}"

    input:
    path transformed_file

    output:
    path "AF_Domain_ids.tsv" 

    script:
    """
    awk 'NR==1 { print "chopping" } \$1 ~ /^[A-Z0-9]+_[0-9][0-9]/ { id = substr(\$1, 1, index(\$1, "_") - 1); print id "/" \$4 }' "${transformed_file}" > AF_Domain_ids.tsv
    """
}