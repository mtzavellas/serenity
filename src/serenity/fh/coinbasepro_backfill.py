from pathlib import Path

import coinbasepro as cbp
import datetime
import fire
import pandas as pd

from serenity.tickstore.tickstore import Tickstore, LocalTickstore, BiTimestamp
from datetime import date, datetime, timedelta
from time import sleep


class CoinbaseHistoricalRatesDownloader:
    def __init__(self, tickstore: Tickstore):
        self.tickstore = tickstore

    def download(self, symbol: str, start_date, end_date):

        client = cbp.PublicClient()

        # if dates passed on command line they will be of type string
        if type(start_date) == str:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if type(end_date) == str:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # start date stepping
        delta = timedelta(days=1)
        while start_date <= end_date:
            all_raw_rates = []

            # load data 4 hours at a time, up until 23:59:00
            for h in range(0, 24, 4):
                start = start_date.strftime('%Y-%m-%d') + ' {:02d}:{:02d}:00.000'.format(h, 0)
                if h + 4 == 24:
                    h = 23
                    end_minute = 59
                else:
                    h = h + 4
                    end_minute = 0
                stop = start_date.strftime('%Y-%m-%d') + ' {:02d}:{:02d}:00.000'.format(h, end_minute)

                print('downloading ' + start + ' - ' + stop)
                raw_rates = client.get_product_historic_rates(symbol, start=start, stop=stop)
                all_raw_rates.extend(raw_rates)
                sleep(1)

            if len(all_raw_rates) > 0:
                # convert one day's data into pandas, and convert all the decimal typed fields
                # from the coinbasepro API into float; h5py doesn't support decimal serialization
                hist_rates = pd.DataFrame(all_raw_rates)
                hist_rates.set_index('time', inplace=True)
                hist_rates['open'] = hist_rates['open'].astype(float)
                hist_rates['high'] = hist_rates['high'].astype(float)
                hist_rates['low'] = hist_rates['low'].astype(float)
                hist_rates['close'] = hist_rates['close'].astype(float)
                hist_rates['volume'] = hist_rates['volume'].astype(float)

                # force ascending sort on time
                hist_rates.sort_index(inplace=True)

                # write HDF5 with compression
                print('writing historical rates to Tickstore')
                self.tickstore.insert(symbol, BiTimestamp(start_date),  hist_rates)

            start_date += delta


def backfill_coinbase_trades(staging_dir: str = '/mnt/raid/data/behemoth/db', symbol: str = 'BTC-USD',
                             start_date=date(2015, 7, 20), end_date=date.today()):
    tickstore = LocalTickstore(Path(staging_dir + '/COINBASE_PRO_ONE_MIN_BINS'), timestamp_column='time')
    downloader = CoinbaseHistoricalRatesDownloader(tickstore)
    downloader.download(symbol, start_date, end_date)
    tickstore.close()


if __name__ == '__main__':
    fire.Fire(backfill_coinbase_trades)
