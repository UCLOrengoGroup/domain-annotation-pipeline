#!/usr/bin/env python3
"""
PDB chopping script that extracts domain segments from PDB structures.
Supports both directory of PDB files and zip archives for efficient processing.
"""
import os
import sys
import subprocess
import argparse
import zipfile
import tempfile
from pathlib import Path
from typing import List, Tuple, Dict, Optional


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


def run_pdb_selres(pdb_content: str, domain_ranges: List[Tuple[int, int]], output_file: str, 
                   append: bool = False, is_file: bool = False) -> None:
    """
    Run pdb_selres on PDB content.
    
    Args:
        pdb_content: PDB file path (if is_file=True) or content as string
        domain_ranges: List of (start, end) residue ranges
        output_file: Path to output file
        append: Whether to append to existing file
        is_file: Whether pdb_content is a file path or content string
    """
    mode = 'a' if append else 'w'
    
    chopping_string = ','.join([f"{start}:{end}" for start, end in domain_ranges])
    
    if is_file:
        # Direct file path - use as-is
        pdb_path = pdb_content
        cleanup_temp = False
    else:
        # Content string - write to temp file
        tmp_fd, pdb_path = tempfile.mkstemp(suffix='.pdb', text=True)
        try:
            with os.fdopen(tmp_fd, 'w') as tmp_file:
                tmp_file.write(pdb_content)
        except:
            os.unlink(pdb_path)
            raise
        cleanup_temp = True
    
    try:
        with open(output_file, mode) as out:
            subprocess.run(
                ['python', '-m', 'pdbtools.pdb_selres', f'-{chopping_string}', pdb_path],
                stdout=out,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=30
            )
    except subprocess.TimeoutExpired:
        print(f"⚠️  Timeout processing {output_file}", file=sys.stderr)
        raise
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Error processing {output_file}: {e.stderr}", file=sys.stderr)
        raise
    finally:
        if cleanup_temp:
            try:
                os.unlink(pdb_path)
            except OSError:
                pass


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
            
            for i, (level, domain_ranges) in enumerate(all_domains, start=1):
                out_file = os.path.join(output_dir, f"{pdb_id}_{i:02d}.pdb")
                run_pdb_selres(pdb_path, domain_ranges, out_file, is_file=True)
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
                    # Extract PDB content from zip (in memory)
                    pdb_bytes = zip_ref.read(zip_contents[pdb_id])
                    pdb_content = pdb_bytes.decode('utf-8', errors='replace')
                    
                    # Combine and sort all domains
                    all_domains = high_domains + med_domains
                    if not all_domains:
                        continue
                    
                    all_domains.sort(key=lambda x: x[1][0][0])
                    
                    for i, (level, domain_ranges) in enumerate(all_domains, start=1):
                        out_file = os.path.join(output_dir, f"{pdb_id}_{i:02d}.pdb")
                        run_pdb_selres(pdb_content, domain_ranges, out_file, is_file=False)
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

