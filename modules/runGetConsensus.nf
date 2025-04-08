/*
 * Run get_consensus.py using the output filenames from runFilterDomains (runFilterDomains.out.collect()).
 * Command format: python get_consensus.py -c filtered_merizo.txt filtered_unidoc.txt filtered_chainsaw.txt -o consensus.tsv
 */
process runGetConsensus {
    container 'domain-annotation-pipeline-ted-tools'
    stageInMode 'copy'
    publishDir './results' , mode: 'copy'

    input:
        path file_name1
        path file_name2
        path file_name3

    output:
        path "consensus.tsv"

    script:
    """
    ${params.getconsensus_script} -c ${file_name1} ${file_name2} ${file_name3} -o consensus.tsv
    """
 }