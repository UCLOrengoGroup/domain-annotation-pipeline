process contrasted_run_annotate {
    label 'sge_low'
    container 'domain-annotation-pipeline-contrasted'
    
    input:
    tuple(val(id), path(md5_file)) // md5_chunks_ch
    path(vector_db)                // contrasted_db_ch   which is S95-v4_4_0.pt
    path(domain_list)              // contrasted_list_ch which is cath-domain-sf-list.txt

    output:
    tuple val(id), path("outputs/annotations/${id}_annotations.tsv"), emit: contrasted_annotations

    script:
    """
    mkdir -p data
    cp -n ${domain_list} data/cath-domain-sf-list.txt

    # create a FASTA file from the md5 input file
    awk -F '\\t' 'NR > 1 {
        pdb = \$1
        sub(/\\.pdb\$/, "", pdb)
        print ">" pdb
        print \$4
    }' ${md5_file} > ${id}.fasta

    # use stored ProstT5 weights if available (run with e.g. --contrasted_hf_home=/SAN/orengolab/bfvd/cache/transformers)
    if [ -n "${params.contrasted_hf_home}" ]; then
	    export HF_HOME="${params.contrasted_hf_home}"
	fi
    
    contrasted-annotate \
    input=${id}.fasta \
    model_path=/opt/contrasted/checkpoints/cath_s40_split.ckpt \
    index=${vector_db}
    """
    }