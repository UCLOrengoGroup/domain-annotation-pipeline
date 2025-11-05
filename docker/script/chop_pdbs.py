import os
import sys
import subprocess

def parse_domain_boundaries(boundary_str, level):
    """Parses a boundary string into a list of (level, [(start, end), ...]) tuples."""
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
            domains.append((level, ranges))
    return domains

def run_pdb_selres(pdb_file, domain_ranges, output_file, append=False):
    mode = 'a' if append else 'w'

    chopping_string = ','.join([f"{start}:{end}" for start, end in domain_ranges])
    with open(output_file, mode) as out:
        subprocess.run(
            ['python', '-m', 'pdbtools.pdb_selres', f'-{chopping_string}', pdb_file],
            stdout=out,
            text=True,
            check=True
        )

def main(consensus_file, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    pdb_dir = os.getcwd()

    with open(consensus_file, 'r') as f:
        for line in f:
            fields = line.strip().split('\t')
            pdb_id = fields[0]
            high_domains = parse_domain_boundaries(fields[6], 'high')
            med_domains = parse_domain_boundaries(fields[7], 'med')

            pdb_path = os.path.join(pdb_dir, f"{pdb_id}.pdb")
            if not os.path.exists(pdb_path):
                print(f"⚠️  PDB not found: {pdb_path}")
                continue

            # Combine and sort all domains by first segment's start
            all_domains = high_domains + med_domains
            all_domains.sort(key=lambda x: x[1][0][0])  # sort by first segment start

            for i, (level, domain_ranges) in enumerate(all_domains, start=1):
                out_file = os.path.join(output_dir, f"{pdb_id}_{i:02}.pdb")
                run_pdb_selres(pdb_path, domain_ranges, out_file)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python chop_pdbs.py <filtered_consensus.tsv> <output_dir>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
