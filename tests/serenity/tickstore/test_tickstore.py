import datetime
import numpy as np
import pandas as pd

from serenity.tickstore.tickstore import LocalTickstore, BiTimestamp
from pathlib import Path


# noinspection DuplicatedCode
def test_tickstore():
    ts_col_name = 'ts'
    tickstore = LocalTickstore(Path('./COINBASE_PRO_ONE_MIN_BINS'), timestamp_column=ts_col_name)

    # ensure we start empty
    assert_empty(tickstore)

    # populate the tickstore for October with random timestamps and integers
    for i in range(31):
        start = pd.to_datetime('2019-10-1')
        end = pd.to_datetime('2019-10-31')
        ts_index = random_dates(start, end, 100)
        ts_index.name = ts_col_name
        ticks = pd.DataFrame(np.random.randint(0, 100, size=(100, 4)), columns=list('ABCD'), index=ts_index)
        tickstore.insert('BTC-USD', BiTimestamp(datetime.date(2019, 10, i+1)), ticks)
        tickstore.insert('ETH-USD', BiTimestamp(datetime.date(2019, 10, i+1)), ticks)

    # close and re-open
    tickstore.close()
    tickstore = LocalTickstore(Path('./COINBASE_PRO_ONE_MIN_BINS'), timestamp_column=ts_col_name)

    # because timestamps are random the number of matches is not deterministic. is there a better way to test this?
    df = tickstore.select('BTC-USD', start=datetime.datetime(2019, 10, 1), end=datetime.datetime(2019, 10, 15))
    assert df.size > 0

    # create a 2nd version of all rows
    for i in range(31):
        start = pd.to_datetime('2019-10-1')
        end = pd.to_datetime('2019-10-31')
        ts_index = random_dates(start, end, 100)
        ts_index.name = ts_col_name
        ticks = pd.DataFrame(np.random.randint(0, 100, size=(100, 4)), columns=list('ABCD'), index=ts_index)
        tickstore.insert('BTC-USD', BiTimestamp(datetime.date(2019, 10, i+1)), ticks)
        tickstore.insert('ETH-USD', BiTimestamp(datetime.date(2019, 10, i+1)), ticks)

    # logically delete all
    for i in range(31):
        tickstore.delete('BTC-USD', BiTimestamp(datetime.date(2019, 10, i+1)))

    assert_empty(tickstore)

    tickstore.close()
    tickstore.destroy()


def assert_empty(tickstore):
    df = tickstore.select('BTC-USD', start=datetime.datetime(2019, 10, 1), end=datetime.datetime(2019, 10, 31))
    assert df.size == 0


def random_dates(start, end, n):
    start_u = start.value//10**9
    end_u = end.value//10**9
    return pd.to_datetime(np.random.randint(start_u, end_u, n), unit='s')
