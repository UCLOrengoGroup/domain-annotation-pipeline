#!/usr/bin/env python

import os
import argparse
import shutil
import tarfile

def count_plddt_scores(file_path):
    plddts = []
    with open(file_path, 'r') as refpdbfile:
        for line in refpdbfile:
            if line[:4] == 'ATOM' and line[12:16] == ' CA ':
                plddts.append(float(line[61:66]))

    if plddts:
        plddts.sort()
        idx20 = len(plddts) // 5
        mean_80_plddt = sum(plddts[idx20:]) / (len(plddts) - idx20)
        mean_plddt = sum(plddts) / len(plddts)
        return mean_plddt, mean_80_plddt
    return None, None

def main():

    parser = argparse.ArgumentParser()
    # Add arguments
    parser.add_argument('pdb_directory', type=str, help='Directory containing PDB files to process')
    parser.add_argument('-o', '--outfile', type=str, required=True, help="Output file")
    parser.add_argument('--plddt_threshold', type=float, default=0.9, required=False, help="If the pLDDT80 is greater than this number, process the domain.")
 #   parser.add_argument('--outdir', type=str, required=True, help="Directory to move pLDDT80 > --plddt_threshold domain PDBs to.")
    # Parse the argument
    args = parser.parse_args()

#    if not os.path.exists(args.outdir):
#        os.mkdir(args.outdir)

    with open(args.outfile, 'w+') as fn:
        for root, _, files in os.walk(args.pdb_directory):
            for file in files:
                if file.endswith('.pdb'):
                    file_path = os.path.join(root, file)
                    mean_plddt, mean_80_plddt = count_plddt_scores(file_path)
                    if mean_plddt is not None:
                        #fn.write(f"{os.path.basename(file)}\t{mean_plddt:.4f}\t{mean_80_plddt:.4f}\n")
                        fn.write(f"{os.path.basename(file)}\t{mean_plddt:.4f}\n")
#                        if mean_80_plddt >= args.plddt_threshold:
#                            shutil.move(file_path, args.outdir)


if __name__=="__main__":
    main()