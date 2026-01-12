process create_md5 {
    label 'sge_low'
    container 'domain-annotation-pipeline-cath-af-cli'

    input:
    tuple val(id), path("pdb/*")
    
    output:
    tuple val(id), path("output_${id}.tsv") 
    
    // added id to intermediate files and dos2unix to recognise end of lines correctly.
    script:
    """
    cath-af-cli pdb-to-md5 -d ./pdb -o output_${id}_tmp.tsv
    dos2unix output_${id}_tmp.tsv > output_${id}.tsv || tr -d '\\r' < output_${id}_tmp.tsv > output_${id}.tsv
    """
}