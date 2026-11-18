"""Exercise fixed and adaptive chunking through the production script's CLI."""

import csv
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "docker" / "script" / "chunk_by_zip.py"


class ChunkByZipTests(unittest.TestCase):
    def run_chunker(self, rows, size, adaptive=False, check=True):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        source = root / "input.tsv"
        source.write_text("".join("\t".join(map(str, row)) + "\n" for row in rows))
        mapping = root / "mapping.tsv"
        command = [
            sys.executable, str(SCRIPT), "--input_file", str(source),
            "--chunk_size", str(size), "--outdir", str(root / "chunks"),
            "--file_list", str(mapping),
        ]
        if adaptive:
            command.append("--adaptive")
        result = subprocess.run(command, capture_output=True, text=True, check=check)
        chunks = []
        if mapping.exists():
            with mapping.open() as handle:
                for row in csv.DictReader(handle, delimiter="\t"):
                    chunks.append((
                        int(row["chunk_id"]), row["zip_name"], row["max_residues"],
                        Path(row["chunk_file"]).read_text().splitlines(),
                    ))
        return chunks, result

    def test_fixed_mode_preserves_existing_order_and_crosses_bands(self):
        chunks, result = self.run_chunker([
            ("c", "b.zip", 1100), ("a", "a.zip", 100),
            ("b", "a.zip", 900), ("c", "a.zip", 200),
        ], 2)
        self.assertEqual(chunks, [
            (0, "a.zip", "200", ["c", "a"]),
            (1, "a.zip", "900", ["b"]),
            (2, "b.zip", "1100", ["c"]),
        ])
        self.assertEqual(result.stdout, "")

    def test_fixed_mode_still_accepts_two_columns(self):
        chunks, _ = self.run_chunker([("b", "a.zip"), ("a", "a.zip")], 10)
        self.assertEqual(chunks, [(0, "a.zip", "", ["a", "b"])])

    def test_adaptive_capacity_scales_and_rounds_down_to_at_least_one(self):
        for baseline in (1, 7, 16, 1000):
            for length, divisor in ((699, 1), (700, 2), (899, 2), (900, 4), (1099, 4), (1100, 8)):
                with self.subTest(baseline=baseline, length=length):
                    capacity = max(1, baseline // divisor)
                    rows = [(f"id{i:04}", "a.zip", length) for i in range(capacity + 1)]
                    chunks, result = self.run_chunker(rows, baseline, adaptive=True)
                    self.assertEqual([len(chunk[3]) for chunk in chunks], [capacity, 1])
                    self.assertCountEqual([pdb_id for chunk in chunks for pdb_id in chunk[3]],
                                          [row[0] for row in rows])
                    self.assertIn(f"capacity={capacity}", result.stdout)

    def test_adaptive_boundaries_order_and_determinism(self):
        lengths = [199, 200, 500, 501, 699, 700, 899, 900, 1099, 1100]
        rows = [(f"id{length}", "a.zip", length) for length in lengths]
        expected = [
            ["id199"], ["id500", "id200"], ["id699", "id501"],
            ["id899", "id700"], ["id1099", "id900"], ["id1100"],
        ]
        chunks, _ = self.run_chunker(rows, 1000, adaptive=True)
        self.assertEqual([chunk[3] for chunk in chunks], expected)
        self.assertEqual([int(chunk[2]) for chunk in chunks], [199, 500, 699, 899, 1099, 1100])
        random.Random(42).shuffle(rows)
        shuffled, _ = self.run_chunker(rows, 1000, adaptive=True)
        self.assertEqual(shuffled, chunks)

    def test_normalised_zips_remain_separate_and_numerically_sorted(self):
        rows = [("id", f"normalised_{number}.zip", 1100) for number in (10, 2)]
        for adaptive in (False, True):
            with self.subTest(adaptive=adaptive):
                chunks, _ = self.run_chunker(rows, 1000, adaptive=adaptive)
                self.assertEqual([chunk[1] for chunk in chunks], ["normalised_2.zip", "normalised_10.zip"])

    def test_adaptive_rejects_missing_lengths(self):
        chunks, result = self.run_chunker([
            ("a", "a.zip", 100), ("b", "a.zip"),
        ], 1000, adaptive=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("requires a residue count for every input row", result.stderr)
        self.assertEqual(chunks, [])

    def test_invalid_baseline_is_rejected(self):
        for size in (0, -1):
            with self.subTest(size=size):
                _, result = self.run_chunker([], size, check=False)
                self.assertEqual(result.returncode, 2)
                self.assertIn("must be positive", result.stderr)

    def test_empty_input_produces_empty_mapping(self):
        chunks, _ = self.run_chunker([], 1000, adaptive=True)
        self.assertEqual(chunks, [])


if __name__ == "__main__":
    unittest.main()
