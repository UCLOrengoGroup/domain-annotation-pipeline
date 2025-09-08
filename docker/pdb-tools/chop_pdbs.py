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

def run_pdb_selres(pdb_file, start, end, output_file, append=False):
    mode = 'a' if append else 'w'
    ignore_lines = ['END', 'ENDMDL', 'MODEL']
    with open(output_file, mode) as out:
        result = subprocess.run(
            ['python', '-m', 'pdbtools.pdb_selres', f'-{start}:{end}', pdb_file],
            capture_output=True,
            text=True,
            check=True
        )
        lines = [line for line in result.stdout.splitlines() if line.split()[0] not in ignore_lines]
        out.write('\n'.join(lines) + '\n')

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
                for j, (start, end) in enumerate(domain_ranges):
                    run_pdb_selres(pdb_path, start, end, out_file, append=(j > 0))
                with open(out_file, 'a') as out_h:
                    out_h.write('END\n')

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python chop_pdbs.py <filtered_consensus.tsv> <output_dir>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
