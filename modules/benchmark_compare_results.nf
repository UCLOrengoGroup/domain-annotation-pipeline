process benchmark_compare_results {
    label 'sge_low'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}"
    publishDir "${params.results_dir}" , mode: 'copy'

    input:
    path final_results
    path expected_results

    output:
    file 'benchmark_differences.tsv'

    script:
    """
    sort ${final_results} > final_results.sorted.tsv
    sort ${expected_results} > expected.sorted.tsv
    diff -u final_results.sorted.tsv expected.sorted.tsv > benchmark_differences.tsv
    """
}