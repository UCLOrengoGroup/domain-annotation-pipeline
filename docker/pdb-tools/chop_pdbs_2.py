import os
import sys
import subprocess

def parse_domain_boundaries(boundary_str):
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
                continue
        if ranges:
            domains.append(ranges)
    return domains

def run_pdb_selres(pdb_file, start, end, output_file, append=False):
    mode = 'a' if append else 'w'
    with open(output_file, mode) as out:
        result = subprocess.run(
            ['python', '-m', 'pdbtools.pdb_selres', f'-{start}:{end}', pdb_file],
            capture_output=True,
            text=True,
            check=True
        )
        lines = [line for line in result.stdout.splitlines() if line.strip() != 'END']
        out.write('\n'.join(lines) + '\n')

def main(consensus_file):
    pdb_dir = os.getcwd()
    output_dir = os.getcwd()

    with open(consensus_file, 'r') as f:
        for line in f:
            if line.startswith("AF-"):
                fields = line.strip().split('\t')
                pdb_id = fields[0]
                high_domains = parse_domain_boundaries(fields[6])
                med_domains = parse_domain_boundaries(fields[7])

                pdb_path = os.path.join(pdb_dir, f"{pdb_id}.pdb")
                if not os.path.exists(pdb_path):
                    print(f"⚠️  PDB not found: {pdb_path}")
                    continue

                for i, domain_ranges in enumerate(high_domains, 1):
                    out_file = os.path.join(output_dir, f"{pdb_id}_high_{i}.pdb")
                    for j, (start, end) in enumerate(domain_ranges):
                        run_pdb_selres(pdb_path, start, end, out_file, append=(j > 0))
                    with open(out_file, 'a') as out_h:
                        out_h.write('END\n')

                for i, domain_ranges in enumerate(med_domains, 1):
                    out_file = os.path.join(output_dir, f"{pdb_id}_med_{i}.pdb")
                    for j, (start, end) in enumerate(domain_ranges):
                        run_pdb_selres(pdb_path, start, end, out_file, append=(j > 0))
                    with open(out_file, 'a') as out_m:
                        out_m.write('END\n')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python chop_pdbs.py <filtered_consensus.tsv>")
        sys.exit(1)
    main(sys.argv[1])
