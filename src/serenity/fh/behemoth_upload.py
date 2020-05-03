import datetime
import logging
from pathlib import Path

import fire
import pandas as pd

from serenity.db import connect_serenity_db, InstrumentCache, TypeCodeCache
from serenity.tickstore.journal import Journal, NoSuchJournalException
from serenity.tickstore.tickstore import LocalTickstore, BiTimestamp
from serenity.utils import init_logging


# noinspection DuplicatedCode
def upload_main(behemoth_path: str = '/behemoth', days_back: int = 1):
    init_logging()
    logger = logging.getLogger(__name__)
    upload_date = datetime.datetime.utcnow().date() - datetime.timedelta(days_back)

    conn = connect_serenity_db()
    conn.autocommit = True
    cur = conn.cursor()

    exchanges = {
        'Phemex': 'PHEMEX_TRADES',
        'CoinbasePro': 'COINBASE_PRO_TRADES',
        'Binance': 'BINANCE_TRADES'
    }
    for exchange, db in exchanges.items():
        instr_cache = InstrumentCache(cur, TypeCodeCache(cur))
        for instrument in instr_cache.get_all_exchange_instruments(exchange):
            symbol = instrument.get_exchange_instrument_code()
            path = Path(f'{behemoth_path}/journals/{db}/{symbol}')
            journal = Journal(path)

            try:
                reader = journal.create_reader(upload_date)

                length = reader.get_length()
                records = []
                while reader.get_pos() < length:
                    time = reader.read_double()
                    sequence = reader.read_long()
                    trade_id = reader.read_long()
                    product_id = reader.read_string()
                    side = 'buy' if reader.read_short() == 0 else 'sell'
                    size = reader.read_double()
                    price = reader.read_double()

                    record = {
                        'time': datetime.datetime.fromtimestamp(time),
                        'sequence': sequence,
                        'trade_id': trade_id,
                        'product_id': product_id,
                        'side': side,
                        'size': size,
                        'price': price
                    }
                    records.append(record)

                if len(records) > 0:
                    logger.info(f'uploading journaled {exchange}/{symbol} ticks to Behemoth for UTC date {str(upload_date)}')
                    df = pd.DataFrame(records)
                    df.set_index('time', inplace=True)
                    logger.info(f'extracted {len(df)} {symbol} trade records')
                    tickstore = LocalTickstore(Path(Path(f'{behemoth_path}/db/{db}')), 'time')
                    tickstore.insert(symbol, BiTimestamp(upload_date), df)
                    tickstore.close()

                    logger.info(f'inserted {len(df)} {symbol} records')
                else:
                    logger.info(f'zero {exchange}/{symbol} ticks for UTC date {str(upload_date)}')
                    tickstore = LocalTickstore(Path(Path(f'{behemoth_path}/db/{db}')), 'time')
                    tickstore.close()
            except NoSuchJournalException:
                logger.error(f'missing journal file: {path}')


if __name__ == '__main__':
    fire.Fire(upload_main)
