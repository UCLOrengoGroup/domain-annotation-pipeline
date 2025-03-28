/*
 * Run get_consensus.py using the output filenames from runFilterDomains (runFilterDomains.out.collect()).
 * Command format: python get_consensus.py -c filtered_merizo.txt filtered_unidoc.txt filtered_chainsaw.txt -o consensus.tsv
 */
process runGetConsensus {
    publishDir './results', mode: 'copy'
    input:
        path file_names

    output:
        path "consensus.tsv"

    script:
    """
    python ${workflow.projectDir}/bin/get_consensus.py -c ${file_names} -o consensus.tsv
    """
 }