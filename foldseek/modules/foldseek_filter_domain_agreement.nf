process foldseek_filter_domain_agreement {
    input:
    tuple path(pdb_file), path(dom_log)

    output:
    path pdb_file, optional: true, emit: passed_domains
    path "dom_failed_domains.tsv", emit: failed_list

    script:
    """
    # Check if Dom agrees this is 1 domain (regardless of continuity)
    if grep -q "1 domains" ${dom_log}; then
        echo "PASS: ${pdb_file} - Dom confirms 1 domain"
        cp ${pdb_file} .
        # Create empty failed list since this one passed
        touch dom_failed_domains.tsv
    else
        echo "FAIL: ${pdb_file} - Dom finds multiple domains"
        echo "${pdb_file}" > dom_failed_domains.tsv
        # Don't copy the PDB file (it will be missing from passed_domains output)
    fi
    """
}
