from mng import MongoReader
from view_ansi import print_table

import sys
try:
    reload(sys)
    sys.setdefaultencoding("utf-8")
except NameError:
    pass  # Python 3 already defaults to utf-8

def show(config):
    "main function"

    default_config = {
        'number_of_ticks': 12,
        'number_of_coins': 10,
        'currency': 'USD',
    }
    int_parameters = [
        'number_of_ticks',
        'number_of_coins',
    ]
    alias = {
        'n': 'number_of_coins',
    }

    for k,v in config.items():
        k = alias.get(k,k)
        default_config[k] = v
        if k in int_parameters:
            try:
                default_config[k] = int(v)
            except:
                pass

    #default_config.update(config)
    config = default_config

    mongo_reader = MongoReader(config)
    data = mongo_reader.load_from_mongo()

    market_cap_direction, vol_24h_direction, btc_dominance_direction = 0, 0, 0
    marktcap_spark = "."*48

    try:
        output = print_table(
                    config['currency'],
                    data,
                    (market_cap_direction, vol_24h_direction, btc_dominance_direction),
                    marktcap_spark)

    except ValueError as e:
        output = "ERROR: %s" % e

    return output
        

