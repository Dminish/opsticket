"""
Bulk-loads a CSV export of historical tickets into the graph, reusing the same
classify + create_ticket pipeline the live API uses.

The archive export carries legacy columns (legacy_id, logged_by, logged_at) that don't exist
in the graph schema — ingesting means picking the fields the model needs (subject,
description) out of that wider structure, same shape as any real archival-content ETL.

Usage:
    python -m scripts.ingest_archive data/archive/tickets.csv
"""

import csv
import sys

from app import graph_client
from app.triage import classify


def ingest(csv_path: str) -> int:
    count = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            subject = row["subject"].strip()
            description = row["description"].strip()
            result = classify(subject, description)
            graph_client.create_ticket(
                subject=subject,
                description=description,
                category=result.category,
                resolver=result.resolver,
            )
            count += 1
    return count


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/archive/tickets.csv"
    n = ingest(path)
    graph_client.close_driver()
    print(f"Ingested {n} tickets from {path}")
