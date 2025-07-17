process join_plddt_md5 {
    label 'local_job'
    publishDir 'results', mode: 'copy'

    input:
    path plDDT_file
    path md5_file
    
    output:
    path "plddt_with_md5.tsv"
        
    script:
    """
    awk 'BEGIN {OFS="\\t"} FNR==NR {md5[\$1]=\$3 ""; next} {printf "%s\\t%s\\t%s\\n", \$1, \$2, md5[\$1]}' ${md5_file} ${plDDT_file} > plddt_with_md5.tsv
    """
}