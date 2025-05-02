# Takes the consensus choppings from filtered_consensus.tsv and applies them to the original pdb files 
# (output from the cif_to_pdb module) to create chopped pdb files which can be used later for the quality
# measures calculations. Uses pdbtools.pdb_selres to edit the files.
import os
import sys
import subprocess

def parse_domain_boundaries(boundary_str):
    """Parses a string like '9-101_227-238,115-220' into a list of domain groups.
    Each group is a list of (start, end) tuples.
    """
    if boundary_str.lower() == 'na':
        return []
    
    domains = []
    for domain_part in boundary_str.split(','):
        ranges = []
        for segment in domain_part.split('_'):
            try:
                start, end = map(int, segment.split('-'))
                ranges.append((start, end))
            except ValueError:
                continue  # Skip malformed entries
        if ranges:
            domains.append(ranges)
    return domains

def run_pdb_selres(pdb_file, start, end, output_file, append=False):
    """Uses pdb_selres from pdb-tools to extract residue range and save to output_file"""
    mode = 'a' if append else 'w'
    with open(output_file, mode) as out:
        result = subprocess.run(
            ['python', '-m', 'pdbtools.pdb_selres', f'-{start}:{end}', pdb_file],
            capture_output=True,
            text=True,
            check=True
        )
# Remove any 'END's
        lines = [line for line in result.stdout.splitlines() if line.strip() != 'END']
        out.write('\n'.join(lines) + '\n')

def main(consensus_file, pdb_dir, output_dir="results/chopped_pdbs"):
    os.makedirs(output_dir, exist_ok=True)

    with open(consensus_file, 'r') as f:
        for line in f:
            if line.startswith("AF-"):  # Skip any headerless noise
                fields = line.strip().split('\t')
                pdb_id = fields[0]
                high_domains = parse_domain_boundaries(fields[6])
                med_domains = parse_domain_boundaries(fields[7])

                pdb_path = os.path.join(pdb_dir, f"{pdb_id}.pdb")
                if not os.path.exists(pdb_path):
                    print(f"⚠️  PDB not found: {pdb_path}")
                    continue

                # Process high-consensus domains
                for i, domain_ranges in enumerate(high_domains, 1):
                    out_file = os.path.join(output_dir, f"{pdb_id}_high_{i}.pdb")
                    for j, (start, end) in enumerate(domain_ranges):
                        run_pdb_selres(pdb_path, start, end, out_file, append=(j > 0))
                    # Now that all fragments are written, add a single END
                    with open(out_file, 'a') as out_h:
                        out_h.write('END\n')
                # Process med-consensus domains
                for i, domain_ranges in enumerate(med_domains, 1):
                    out_file = os.path.join(output_dir, f"{pdb_id}_med_{i}.pdb")
                    for j, (start, end) in enumerate(domain_ranges):
                        run_pdb_selres(pdb_path, start, end, out_file, append=(j > 0))
                    # Now that all fragments are written, add a single END
                    with open(out_file, 'a') as out_m:
                        out_m.write('END\n')

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python chop_pdbs.py <consensus.tsv> <pdb_dir>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])