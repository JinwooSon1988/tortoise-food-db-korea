#!/usr/bin/env python3
"""One-command ingestion of finished broad + per-taxon OpenAlex checkpoints.

Writes a site-ready index to a separate output; does not deploy, grade, or
overwrite the existing research index unless the caller explicitly chooses it.
"""
import argparse
import json
from pathlib import Path
from convert_broad_openalex_leads import convert
from merge_openalex_leads import build

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--broad', type=Path, required=True)
    p.add_argument('--per-taxon', type=Path)
    p.add_argument('--existing', type=Path, default=Path(__file__).resolve().parents[1] / 'data/research_source_leads_index.json')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.resolve() == args.existing.resolve():
        p.error('Output must be separate from existing index to allow review.')
    if not args.broad.exists():
        p.error('Broad checkpoint does not exist: ' + str(args.broad))
    broad, broad_stats = convert(args.broad)
    if not broad_stats['pages_processed']:
        p.error('No successful broad pages to ingest.')
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as tmp:
        combined = Path(tmp) / 'combined.jsonl'
        with combined.open('w', encoding='utf-8') as dest:
            if args.per_taxon and args.per_taxon.exists():
                with args.per_taxon.open(encoding='utf-8') as stream:
                    for line in stream:
                        try:
                            row = json.loads(line)
                            if row.get('status') == 'searched':
                                dest.write(json.dumps(row, ensure_ascii=False) + '\n')
                        except ValueError:
                            continue
            for row in broad:
                dest.write(json.dumps(row, ensure_ascii=False) + '\n')
        result, stats = build(combined, args.existing)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    print(json.dumps({'broad': broad_stats, 'merged': stats, 'output': str(args.output),
                      'safety_grades_changed': 0, 'deployed': False},
                     ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
