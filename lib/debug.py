from mng import MongoReader, MongoWriter

MONGO_READER = MongoReader()
MONGO_WRITER = MongoWriter()

import json

time_start = 1552655494 - 3600
time_end = 1553001094

entries = MONGO_READER.get_raw_data(
    "BTC", time_start, time_end, collection_name="coins"
)
# print entries[0]
print(len(list(entries)))
