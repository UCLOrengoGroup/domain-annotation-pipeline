#!/usr/bin/env python3
"""
PDB chopping script that extracts domain segments from PDB structures.
Supports both directory of PDB files and zip archives for efficient processing.
"""
import os
import sys
import argparse
import zipfile
from pathlib import Path
from typing import List, Tuple, Dict, Optional

from pdbtools import pdb_selres

# pdb-tools exposes the residue-selection generator as run() in modern releases
# (and select_residues() in older ones); support both. Signature is identical:
# (fhandle_line_iterator, residue_number_set) -> yields PDB line strings.
_selres = getattr(pdb_selres, "run", None) or getattr(pdb_selres, "select_residues")


def parse_domain_boundaries(boundary_str: str, level: str) -> List[Tuple[str, List[Tuple[int, int]]]]:
    """
    Parses a boundary string into a list of (level, [(start, end), ...]) tuples.
    
    Args:
        boundary_str: Domain boundary string (e.g., "1-50_60-100,101-150")
        level: Domain confidence level ('high' or 'med')
    
    Returns:
        List of tuples containing level and residue ranges
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
                continue
        if ranges:
            domains.append((level, ranges))
    return domains


def _residue_set(domain_ranges: List[Tuple[int, int]]) -> set:
    """Expand [(start, end), ...] inclusive ranges into a set of residue numbers."""
    residues = set()
    for start, end in domain_ranges:
        residues.update(range(start, end + 1))
    return residues


def write_domain(pdb_lines: List[str], domain_ranges: List[Tuple[int, int]], output_file: str) -> None:
    """
    Write a single chopped domain by selecting residues in-process.

    Reuses pdb-tools' own residue-selection generator (pdb_selres) so the output is
    identical to the previous `python -m pdbtools.pdb_selres` subprocess, but avoids
    launching a Python interpreter per domain and re-writing a temp file per domain.

    Args:
        pdb_lines: The structure's PDB lines (split once per structure; re-iterable list).
        domain_ranges: List of (start, end) inclusive residue ranges for this domain.
        output_file: Path to write the chopped domain PDB.
    """
    residues = _residue_set(domain_ranges)
    # Pass a fresh iterator per call since the generator consumes it.
    with open(output_file, 'w') as out:
        out.writelines(_selres(iter(pdb_lines), residues))


def process_from_directory(consensus_file: str, pdb_dir: str, output_dir: str) -> Tuple[int, int, int]:
    """
    Process PDB files from a directory.
    
    Returns:
        Tuple of (consensus_count, processed_count, missing_count)
    """
    consensus_count = 0
    processed_count = 0
    missing_count = 0
    
    with open(consensus_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            consensus_count += 1
            fields = line.split('\t')
            
            if len(fields) < 8:
                continue
            
            pdb_id = fields[0]
            high_domains = parse_domain_boundaries(fields[6], 'high')
            med_domains = parse_domain_boundaries(fields[7], 'med')
            
            pdb_path = os.path.join(pdb_dir, f"{pdb_id}.pdb")
            if not os.path.exists(pdb_path):
                print(f"⚠️  PDB not found: {pdb_path}", file=sys.stderr)
                missing_count += 1
                continue
            
            # Combine and sort all domains by first segment's start
            all_domains = high_domains + med_domains
            if not all_domains:
                continue
                
            all_domains.sort(key=lambda x: x[1][0][0])

            # Read the structure once, then slice each domain from it in-process.
            with open(pdb_path, 'r', encoding='utf-8') as pf:
                pdb_lines = pf.readlines()

            for i, (level, domain_ranges) in enumerate(all_domains, start=1):
                out_file = os.path.join(output_dir, f"{pdb_id}_{i:02d}.pdb")
                write_domain(pdb_lines, domain_ranges, out_file)
                processed_count += 1
    
    return consensus_count, processed_count, missing_count


def process_from_zip(consensus_file: str, pdb_zip: str, output_dir: str) -> Tuple[int, int, int, int]:
    """
    Process PDB files from a zip archive.
    
    Returns:
        Tuple of (consensus_count, processed_count, missing_count, error_count)
    """
    consensus_count = 0
    processed_count = 0
    missing_count = 0
    error_count = 0
    
    with zipfile.ZipFile(pdb_zip, 'r') as zip_ref:
        # Build lookup dictionary
        zip_contents: Dict[str, str] = {Path(name).stem: name for name in zip_ref.namelist()}
        
        with open(consensus_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                
                consensus_count += 1
                fields = line.split('\t')
                
                if len(fields) < 8:
                    print(f"⚠️  Line {line_num}: insufficient fields ({len(fields)} < 8)", file=sys.stderr)
                    continue
                
                pdb_id = fields[0]
                
                try:
                    high_domains = parse_domain_boundaries(fields[6], 'high')
                    med_domains = parse_domain_boundaries(fields[7], 'med')
                except (IndexError, ValueError) as e:
                    print(f"⚠️  Line {line_num}: error parsing boundaries for {pdb_id}: {e}", file=sys.stderr)
                    error_count += 1
                    continue
                
                if pdb_id not in zip_contents:
                    print(f"⚠️  PDB not found in zip: {pdb_id}.pdb", file=sys.stderr)
                    missing_count += 1
                    continue
                
                try:
                    # Extract PDB content from zip (in memory) and split once per structure.
                    pdb_bytes = zip_ref.read(zip_contents[pdb_id])
                    pdb_content = pdb_bytes.decode('utf-8', errors='replace')
                    pdb_lines = pdb_content.splitlines(keepends=True)

                    # Combine and sort all domains
                    all_domains = high_domains + med_domains
                    if not all_domains:
                        continue

                    all_domains.sort(key=lambda x: x[1][0][0])

                    for i, (level, domain_ranges) in enumerate(all_domains, start=1):
                        out_file = os.path.join(output_dir, f"{pdb_id}_{i:02d}.pdb")
                        write_domain(pdb_lines, domain_ranges, out_file)
                        processed_count += 1
                        
                except (zipfile.BadZipFile, KeyError, UnicodeDecodeError) as e:
                    print(f"⚠️  Error reading {pdb_id} from zip: {e}", file=sys.stderr)
                    error_count += 1
                    continue
                except Exception as e:
                    print(f"⚠️  Unexpected error processing {pdb_id}: {e}", file=sys.stderr)
                    error_count += 1
                    continue
    
    return consensus_count, processed_count, missing_count, error_count


def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='Chop PDB structures into domain segments based on consensus boundaries.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process from directory of PDB files
  %(prog)s --consensus consensus.tsv --pdb-dir ./pdbs --output ./domains
  
  # Process from zip archive (faster for shared filesystems)
  %(prog)s --consensus consensus.tsv --pdb-zip pdbs.zip --output ./domains
  
  # Legacy positional arguments (deprecated)
  %(prog)s consensus.tsv output_dir
        """
    )
    
    parser.add_argument('--consensus', '-c', 
                        help='Path to consensus TSV file')
    parser.add_argument('--pdb-dir', '-d',
                        help='Directory containing PDB files')
    parser.add_argument('--pdb-zip', '-z',
                        help='Zip file containing PDB files')
    parser.add_argument('--output', '-o',
                        help='Output directory for chopped domain PDB files')
    
    # Support legacy positional arguments for backward compatibility
    parser.add_argument('legacy_consensus', nargs='?',
                        help=argparse.SUPPRESS)
    parser.add_argument('legacy_output', nargs='?',
                        help=argparse.SUPPRESS)
    
    args = parser.parse_args()
    
    # Handle legacy positional arguments
    if args.legacy_consensus and args.legacy_output:
        consensus_file = args.legacy_consensus
        output_dir = args.legacy_output
        pdb_source = os.getcwd()  # Use current directory for PDB files
        use_zip = False
    else:
        # Use named arguments
        if not args.consensus or not args.output:
            parser.error("--consensus and --output are required")
        
        if not args.pdb_dir and not args.pdb_zip:
            parser.error("Either --pdb-dir or --pdb-zip must be specified")
        
        if args.pdb_dir and args.pdb_zip:
            parser.error("Cannot specify both --pdb-dir and --pdb-zip")
        
        consensus_file = args.consensus
        output_dir = args.output
        pdb_source = args.pdb_zip if args.pdb_zip else args.pdb_dir
        use_zip = bool(args.pdb_zip)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process based on input type
    if use_zip:
        consensus_count, processed_count, missing_count, error_count = process_from_zip(
            consensus_file, pdb_source, output_dir
        )
        print(f"✓ Processed {consensus_count} consensus entries, generated {processed_count} domain files")
        if missing_count > 0:
            print(f"⚠️  {missing_count} PDB files not found in zip", file=sys.stderr)
        if error_count > 0:
            print(f"⚠️  {error_count} errors during processing", file=sys.stderr)
        
        if error_count > 0 or (processed_count == 0 and missing_count > 0):
            sys.exit(1)
    else:
        consensus_count, processed_count, missing_count = process_from_directory(
            consensus_file, pdb_source, output_dir
        )
        print(f"✓ Processed {consensus_count} consensus entries, generated {processed_count} domain files")
        if missing_count > 0:
            print(f"⚠️  {missing_count} PDB files not found", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"✗ Fatal error: {e}", file=sys.stderr)
        sys.exit(1)

