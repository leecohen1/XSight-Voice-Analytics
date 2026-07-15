#!/usr/bin/env python3
"""One-time normalization pass for data/historical_sales_calls.csv (Phase 5C
refinement): overwrites `speaking_rate_wpm` and `price_mentions_count` with
values computed by the canonical algorithms in validate_historical_dataset.py
(compute_word_counts / PRICE_KEYWORDS), which are now the single source of
truth for those two fields.

Does NOT touch: transcript, metadata, Ground Truth fields, outcomes, intent,
objections, sentiment, scores, manager_notes, or any other computed field
(silence_ratio, speech_to_non_speech_ratio, agent_talk_ratio,
competitor_mentions_count, call_duration_seconds) — none of those had a
validator-identified mismatch, so they are left exactly as authored.

Usage:
    python scripts/normalize_dataset_fields.py

Prints a diff of every value it changes, then re-writes the CSV in place.
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_historical_dataset import (  # noqa: E402
    ROOT, CSV_PATH, EXPECTED_COLUMNS, load_csv,
    recompute_speaking_rate_wpm, recompute_price_mentions_count,
)


def main():
    header, rows = load_csv()
    if header != EXPECTED_COLUMNS:
        print("ERROR: CSV header does not match expected schema — aborting normalization.")
        return 1

    changes = []
    for r in rows:
        cid = r["call_id"]

        new_wpm = round(recompute_speaking_rate_wpm(r["transcript"], r["call_duration_seconds"]))
        old_wpm = r["speaking_rate_wpm"]
        if str(new_wpm) != old_wpm:
            changes.append(f"{cid}: speaking_rate_wpm {old_wpm} -> {new_wpm}")
            r["speaking_rate_wpm"] = str(new_wpm)

        new_price = recompute_price_mentions_count(r["transcript"])
        old_price = r["price_mentions_count"]
        if str(new_price) != old_price:
            changes.append(f"{cid}: price_mentions_count {old_price} -> {new_price}")
            r["price_mentions_count"] = str(new_price)

    print(f"Normalizing {CSV_PATH.relative_to(ROOT)} ...")
    print(f"{len(changes)} field value(s) changed:\n")
    for c in changes:
        print(f"  - {c}")

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"\nCSV rewritten with {len(rows)} rows, {len(EXPECTED_COLUMNS)} columns unchanged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
