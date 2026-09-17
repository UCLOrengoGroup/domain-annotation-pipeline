process restore_final_results {
    label 'sge_low'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}"
    publishDir "${params.results_dir}", mode: 'copy'

    input:
    path final_results
    path resmap_zips
    path restore_script

    output:
    path "restored_final_results.tsv"

    script:
    def unzip_commands = resmap_zips.collect {"unzip -q ${it} -d resmaps"}.join('\n')
    """
    mkdir -p resmaps
    ${unzip_commands}

    python3 ${restore_script} \
        --final_results "${final_results}" \
        --resmap_dir resmaps \
        --output restored_final_results.tsv
    """
}