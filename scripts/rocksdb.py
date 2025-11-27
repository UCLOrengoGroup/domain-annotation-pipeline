#!/usr/bin/env python3

# pip install plyvel tqdm
# python script.py build --tar mydata.tar.gz --db my_leveldb
# python script.py extract --db my_leveldb --ids ids.txt --out output_dir


import os
import tarfile
import plyvel
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm


def open_tarfile(tar_path):
    if tar_path.endswith(".tar.gz") or tar_path.endswith(".tgz"):
        return tarfile.open(tar_path, "r:gz")
    elif tar_path.endswith(".tar"):
        return tarfile.open(tar_path, "r")
    else:
        raise ValueError(f"Unsupported archive format: {tar_path}")


def build_leveldb_from_tar(tar_path, db_path, max_workers=os.cpu_count()):
    """Build a LevelDB (via plyvel) from a tar or tar.gz archive."""

    db = plyvel.DB(db_path, create_if_missing=True)

    with open_tarfile(tar_path) as tar:
        members = [m for m in tar.getmembers() if m.isfile()]

    def process_member(member):
        with open_tarfile(tar_path) as tar_local:
            file_obj = tar_local.extractfile(member)
            if file_obj:
                content = file_obj.read()
                db.put(member.name.encode("utf-8"), content)
                return member.name
        return None

    print(f"[+] Indexing {len(members)} files into LevelDB from '{tar_path}'...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        list(tqdm(executor.map(process_member, members), total=len(members)))

    db.close()
    print("[✓] LevelDB build complete.")


def extract_files_by_ids(db_path, output_dir, ids, max_workers=os.cpu_count()):
    """Extract files from LevelDB into output directory based on list of keys."""

    os.makedirs(output_dir, exist_ok=True)
    db = plyvel.DB(db_path, create_if_missing=False)

    def extract_and_write(file_id):
        key = file_id.encode("utf-8")
        value = db.get(key)
        if value is None:
            return f"Missing: {file_id}"
        output_path = os.path.join(output_dir, file_id)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(value)
        return f"Extracted: {file_id}"

    print(f"[+] Extracting {len(ids)} files into '{output_dir}'...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        list(tqdm(executor.map(extract_and_write, ids), total=len(ids)))

    db.close()
    print("[✓] Extraction complete.")


# CLI
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="LevelDB builder and extractor (via plyvel)."
    )
    subparsers = parser.add_subparsers(dest="command")

    # Build command
    build_parser = subparsers.add_parser(
        "build", help="Build LevelDB from tar or tar.gz"
    )
    build_parser.add_argument(
        "--tar", required=True, help="Path to tar or tar.gz archive"
    )
    build_parser.add_argument("--db", required=True, help="Path to output LevelDB")

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract files by ID")
    extract_parser.add_argument("--db", required=True, help="Path to LevelDB")
    extract_parser.add_argument(
        "--ids", required=True, help="Path to text file with IDs (one per line)"
    )
    extract_parser.add_argument("--out", required=True, help="Output directory")

    args = parser.parse_args()

    if args.command == "build":
        build_leveldb_from_tar(args.tar, args.db)
    elif args.command == "extract":
        with open(args.ids) as f:
            ids = [line.strip() for line in f if line.strip()]
        extract_files_by_ids(args.db, args.out, ids)
