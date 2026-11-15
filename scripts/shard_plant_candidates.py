#!/usr/bin/env python3
"""Deterministically partition identity-only plant NDJSON into worker queues.

Partitions are stable across input order and machine count. No feeding verdicts.
Usage: python scripts/shard_plant_candidates.py staged.jsonl --output-dir queues --shards 32
"""
import argparse
import hashlib
import json
from pathlib import Path


def shard(input_path, output_dir, shards):
    if not 1 <= shards <= 256:
        raise ValueError("shards must be between 1 and 256")
    if output_dir.resolve() == input_path.resolve() or output_dir.resolve() in input_path.resolve().parents:
        raise ValueError("output directory conflicts with input")
    output_dir.mkdir(parents=True, exist_ok=True)
    # Refuse to overwrite existing queues to avoid mixing runs.
    destinations = [output_dir / f"queue-{i:03d}.jsonl" for i in range(shards)]
    if any(path.exists() for path in destinations):
        raise FileExistsError("queue output already exists; use a fresh directory")
    files = []
    counts = [0] * shards
    seen = set()
    try:
        for path in destinations:
            files.append(path.open("x", encoding="utf-8"))
        with input_path.open(encoding="utf-8") as source:
            for line_number, line in enumerate(source, 1):
                if not line.strip():
                    continue
                item = json.loads(line)
                if not isinstance(item, dict) or item.get("feed_review_status") != "identity_only":
                    raise ValueError(f"line {line_number}: identity_only record required")
                cid = item.get("candidate_id")
                if not isinstance(cid, str) or not cid:
                    raise ValueError(f"line {line_number}: candidate_id required")
                if cid in seen:
                    raise ValueError(f"line {line_number}: duplicate candidate_id")
                seen.add(cid)
                index = int.from_bytes(hashlib.sha256(cid.encode("utf-8")).digest()[:8], "big") % shards
                files[index].write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
                counts[index] += 1
    except Exception:
        for f in files:
            f.close()
        for path in destinations:
            path.unlink(missing_ok=True)
        raise
    finally:
        for f in files:
            if not f.closed:
                f.close()
    manifest = {"schema_version": 1, "shards": shards, "total": sum(counts),
                "counts": counts, "status": "identity_only", "note": "Review queues only; no feeding claims."}
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--shards", type=int, default=32)
    args = parser.parse_args()
    print(json.dumps(shard(args.input, args.output_dir, args.shards), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
