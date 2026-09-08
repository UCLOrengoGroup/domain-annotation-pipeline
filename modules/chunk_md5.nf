process chunk_md5 {
    label 'sge_low'
    container "ghcr.io/uclorengogroup/domain-annotation-pipeline-script:${params.container_tag_name}" 
    publishDir "${params.results_dir}/intermediate", mode: 'copy', enabled: params.debug

    input:
    path md5_file
    val chunk_size

    output:
    path "md5_chunk_*.tsv", emit: chunks

    script:
    """
    header=\$(head -n 1 ${md5_file})

    tail -n +2 ${md5_file} | split -l ${chunk_size} -d -a 5 - chunk_

    for f in chunk_*; do
        id=\$(echo "\$f" | sed 's/chunk_//')
        { printf "%s\\n" "\$header"; cat "\$f";} > md5_chunk_\${id}.tsv
        rm "\$f"
    done
    """
}

