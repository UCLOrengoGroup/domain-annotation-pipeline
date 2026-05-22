process contrasted_run_annotate {
    label 'sge_low'
    container 'domain-annotation-pipeline-contrasted'
    
    input:
    tuple val(id), path(md5_file), path(vector_db), path(domain_list) // vector_db is S95-v4_4_0.pt

    output:
    tuple val(id), path("${id}_annotations.tsv"), emit: contrasted_annotations

    script:
    """
    cp -n ${domain_list} data

    # create a FASTA file from the md5 input file
    awk -F '\\t' 'NR > 1 {
        pdb = \$1
        sub(/\\.pdb$/, "", pdb)
        print ">" pdb
        print \$4
    }' ${md5_file} > ${id}.fasta

    contrasted-annotate \
    input=${id}.fasta \
    model_path=checkpoints/cath_s40_split.ckpt \
    index=${vector_db}
    """
    }