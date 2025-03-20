"""
This is a helper script that removes the data anomaly from December 2021 in all collections.
"""

import json
from bson import json_util

from pymongo import MongoClient

def get_entries_above_threshold_as_json(db_name: str, collection_name: str) -> str:
    """Retrieves all entries from a MongoDB collection where price_usd > 1000000000 and returns them as formatted JSON.

    Args:
        db_name (str): Name of the database.
        collection_name (str): Name of the collection.

    Returns:
        str: A JSON string that represents all entries from the specified collection where price_usd > 1000000000.
    
    Raises:
        Exception: If there is an issue connecting to the database or retrieving the entries.
    """
    try:
        client = MongoClient()
        db = client[db_name]
        collection = db[collection_name]

        query = {
            # "price_usd.max": {"$gt": 10000000},
            "price_usd": {"$gt": 10000000},
            # "symbol": "BTC",
            "timestamp": {
                "$gte": 1638748800,  # 06 Dec 2021
                "$lt": 1640476800    # 26 Dec 2021
            }
        }

        # Delete all entries matching the query
        # entries = collection.delete_many(query)
        collection.delete_many(query)
        entries = collection.find(query)

        # Convert the BSON documents to a list of JSON strings
        json_entries = json.dumps(list(entries), default=json_util.default, indent=4)

        return json_entries
    except Exception as e:
        raise Exception(f"An error occurred while retrieving the entries: {e}")

def main():
    db_name = "ratesx"
    # collection_name = "coins_1h"
    collection_name = "coins"
    print(get_entries_above_threshold_as_json(db_name, collection_name))

if __name__ == "__main__":
    main()
