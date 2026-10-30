"""
This is a helper script that removes duplicate coin entries (issue #94).

CoinMarketCap can list several tokens with the same ticker (e.g. a second
"BTC" priced at a few cents). Until the collector deduplicated them, all of
them were stored in the `coins` collection with the same (symbol, timestamp),
and the readers mixed their prices (low spikes on the chart, wrong change).

For every (symbol, timestamp) group in `coins` with more than one document,
the document with the lowest `rank` is kept and all others are deleted.

By default the script only prints what it would delete (dry run).
Pass --apply to actually delete.

Aggregated collections:

    `coins_1h` is written by lib/aggregate.py with replace_one() keyed on
    (symbol, timestamp) and has a unique index on these fields. So it has no
    duplicates to remove: each document was aggregated from the mixed raw
    data and its min/max/avg/begin/end values are already wrong. It cannot be
    fixed by deduplication and has to be re-aggregated.

    With --purge-aggregated, the script also deletes the `coins_1h` documents
    of the affected symbols starting one interval before the first duplicate.
    aggregate_new_entries() resumes from the last aggregated timestamp of a
    symbol, so the next run of lib/aggregate.py rebuilds them from the
    cleaned raw data. Run the aggregator right after this script.

    `coins_24h` is neither written nor read by the current code (the 24h
    interval is disabled in lib/aggregate.py), so it is left alone.

Usage:

    python lib/fix_duplicate_symbols.py [--apply] [--purge-aggregated] [SYMBOL ...]
"""

import argparse
import os
from collections import Counter

from pymongo import MongoClient

AGGREGATED_COLLECTION = "coins_1h"
AGGREGATED_INTERVAL = 3600
DELETE_BATCH_SIZE = 1000


def find_duplicates(collection, symbols=None):
    """Yields (symbol, timestamp, ids_to_delete) for every duplicated group."""

    pipeline = []
    if symbols:
        pipeline.append({"$match": {"symbol": {"$in": symbols}}})
    pipeline += [
        {
            "$group": {
                "_id": {"symbol": "$symbol", "timestamp": "$timestamp"},
                "docs": {"$push": {"_id": "$_id", "rank": "$rank"}},
                "count": {"$sum": 1},
            }
        },
        {"$match": {"count": {"$gt": 1}}},
    ]

    for group in collection.aggregate(pipeline, allowDiskUse=True):
        docs = sorted(
            group["docs"],
            key=lambda x: (x.get("rank") is None, x.get("rank")),
        )
        yield (
            group["_id"]["symbol"],
            group["_id"]["timestamp"],
            [x["_id"] for x in docs[1:]],
        )


def delete_ids(collection, ids):
    deleted = 0
    for i in range(0, len(ids), DELETE_BATCH_SIZE):
        result = collection.delete_many({"_id": {"$in": ids[i : i + DELETE_BATCH_SIZE]}})
        deleted += result.deleted_count
    return deleted


def main():
    parser = argparse.ArgumentParser(
        description="Remove duplicate (symbol, timestamp) entries from ratesx.coins"
    )
    parser.add_argument(
        "--apply", action="store_true", help="delete the duplicates (default: dry run)"
    )
    parser.add_argument(
        "--purge-aggregated",
        action="store_true",
        help="also delete affected %s entries so that lib/aggregate.py rebuilds them"
        % AGGREGATED_COLLECTION,
    )
    parser.add_argument("symbols", nargs="*", help="limit to these symbols")
    args = parser.parse_args()

    client = MongoClient(host=os.environ.get("MONGO_HOST", "localhost"))
    db = client.ratesx

    to_delete = []
    counts = Counter()
    first_timestamp = {}
    for symbol, timestamp, ids in find_duplicates(db.coins, args.symbols):
        to_delete += ids
        counts[symbol] += len(ids)
        if symbol not in first_timestamp or timestamp < first_timestamp[symbol]:
            first_timestamp[symbol] = timestamp

    mode = "deleting" if args.apply else "dry run, would delete"
    for symbol, count in counts.most_common():
        print(
            "coins: %s: %s %s duplicate entries (first at %s)"
            % (symbol, mode, count, int(first_timestamp[symbol]))
        )
    print("coins: %s %s entries in total" % (mode, len(to_delete)))

    if args.apply:
        print("coins: deleted %s entries" % delete_ids(db.coins, to_delete))

    if args.purge_aggregated:
        aggregated = db[AGGREGATED_COLLECTION]
        for symbol, timestamp in sorted(first_timestamp.items()):
            query = {
                "symbol": symbol,
                "timestamp": {"$gt": timestamp - AGGREGATED_INTERVAL},
            }
            if args.apply:
                count = aggregated.delete_many(query).deleted_count
            else:
                count = aggregated.count_documents(query)
            print("%s: %s: %s %s entries" % (AGGREGATED_COLLECTION, symbol, mode, count))


if __name__ == "__main__":
    main()
