import os
import tarfile
import rocksdb
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


def build_rocksdb_from_tar(tar_path, db_path, max_workers=os.cpu_count()):
    """Build RocksDB from a tar archive using filename as key."""

    opts = rocksdb.Options()
    opts.create_if_missing = True
    opts.IncreaseParallelism(max_workers)
    opts.OptimizeForPointLookup(1024)
    db = rocksdb.DB(db_path, opts)

    with tarfile.open(tar_path, "r") as tar:
        members = [m for m in tar.getmembers() if m.isfile()]

    def process_member(member):
        with tarfile.open(tar_path, "r") as tar_local:
            file_obj = tar_local.extractfile(member)
            if file_obj:
                content = file_obj.read()
                db.put(member.name.encode("utf-8"), content)
                return member.name
        return None

    print(f"[+] Indexing {len(members)} files into RocksDB...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        list(tqdm(executor.map(process_member, members), total=len(members)))

    print("[✓] RocksDB build complete.")


def extract_files_by_ids(db_path, output_dir, ids, max_workers=os.cpu_count()):
    """Extract files from RocksDB into output directory based on list of keys."""

    os.makedirs(output_dir, exist_ok=True)

    opts = rocksdb.Options()
    opts.create_if_missing = False
    db = rocksdb.DB(db_path, opts, read_only=True)

    def extract_and_write(file_id):
        key = file_id.encode("utf-8")
        value = db.get(key)
        if value is None:
            return f"Missing: {file_id}"
        output_path = os.path.join(output_dir, file_id)
        with open(output_path, "wb") as f:
            f.write(value)
        return f"Extracted: {file_id}"

    print(f"[+] Extracting {len(ids)} files into '{output_dir}'...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(tqdm(executor.map(extract_and_write, ids), total=len(ids)))

    print("[✓] Extraction complete.")


# Example usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RocksDB builder and extractor.")
    subparsers = parser.add_subparsers(dest="command")

    # Build command
    build_parser = subparsers.add_parser("build", help="Build RocksDB from tar")
    build_parser.add_argument("--tar", required=True, help="Path to tar archive")
    build_parser.add_argument("--db", required=True, help="Path to output RocksDB")

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract files by ID")
    extract_parser.add_argument("--db", required=True, help="Path to RocksDB")
    extract_parser.add_argument(
        "--ids", required=True, help="Path to text file with IDs (one per line)"
    )
    extract_parser.add_argument("--out", required=True, help="Output directory")

    args = parser.parse_args()

    if args.command == "build":
        build_rocksdb_from_tar(args.tar, args.db)
    elif args.command == "extract":
        with open(args.ids) as f:
            ids = [line.strip() for line in f if line.strip()]
        extract_files_by_ids(args.db, args.out, ids)
