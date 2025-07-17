process run_unidoc {
    label 'sge_job'
    container 'domain-annotation-pipeline-unidoc'

    input:
    path '*'

    output:
    path 'unidoc_results.csv'

    script:
    """
    set -e

    # UniDoc expects to be run from current directory
    ln -s ${params.unidoc_dir}/stride .
    ln -s ${params.unidoc_dir}/UniDoc_struct .

    for pdb_file in *.pdb; do
        file_stem=\${pdb_file%.pdb}

        ${params.unidoc_script} -i \$pdb_file -c A -o \${file_stem}.unidoc

        # extract the chopping from the last line of the unidoc output (possibly blank)
        # and change chopping string to the expected format
        chopping=\$(tail -n 1 \${file_stem}.unidoc | tr '~' '-' | tr ',' '_' | tr '/' ',' | tr -d '\\n')

        echo "\$file_stem\t\$chopping" >> unidoc_results.csv
    done
    """
}