import datetime
import logging
import os.path
import re
import shutil

from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import Tuple

import pandas as pd


class BiTimestamp:
    """
    A bitemporal timestamp combining as-at time and as-of time.
    """

    # cannot use datetime.min / datetime.max due to limitations
    # see https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#representing-out-of-bounds-spans
    start_as_of = pd.Timestamp.min.to_pydatetime(warn=False)
    latest_as_of = pd.Timestamp.max.to_pydatetime(warn=False)

    def __init__(self, as_at_date: datetime.date, as_of_time: datetime.datetime = latest_as_of):
        self.as_at_date = as_at_date
        self.as_of_time = as_of_time
        pass

    def as_at(self) -> datetime.date:
        return self.as_at_date

    def as_of(self) -> datetime.datetime:
        return self.as_of_time

    def __str__(self) -> str:
        return str((self.as_at_date, self.as_of_time))


class Tickstore(ABC):
    """
    Base class for all implementations of tickstores.
    """

    @abstractmethod
    def select(self, symbol: str, start: datetime.datetime, end: datetime.datetime,
               as_of_time: datetime.datetime = BiTimestamp.latest_as_of) -> pd.DataFrame:
        """
        Selects all ticks between start and end timestamps, optionally restricted to version effective as of as_of_time.
        :return: a DataFrame with the content matching the query
        """
        pass

    @abstractmethod
    def insert(self, symbol: str, ts: BiTimestamp, ticks: pd.DataFrame):
        """
        For a given symbol insert ticks at the given date, either newly creating an entry if none for
        that date or logically overwriting by creating a new version of the ticks for that date.
        """
        pass

    @abstractmethod
    def delete(self, symbol: str, ts: BiTimestamp):
        """
        For a given symbol and date logically delete its content effective now.
        """
        pass

    def flush(self):
        """
        Writes to disk, uploads data or otherwise commits any transient state without fully closing the store.
        """
        pass

    @abstractmethod
    def close(self):
        """
        Releases any resources associated with the tickstore.
        """
        pass

    @abstractmethod
    def destroy(self):
        """
        Destroys the entire tickstore.
        """
        pass


class DataFrameIndex:
    """
    HDF5- and Pandas-based multi-level index used by LocalTickstore.
    """

    logger = logging.getLogger(__name__)

    def __init__(self, base_path: Path, index_path: Path, table_name: str):
        self.base_path = base_path
        self.index_path = index_path
        self.table_name = table_name
        self.dirty = False

        if not self.index_path.exists():
            self.logger.info(f'rebuilding {self.index_path}')
            self._build_index()
        else:
            # noinspection PyTypeChecker
            existing_index: pd.DataFrame = pd.read_hdf(str(self.index_path))
            self.df = existing_index

    def select(self, symbol: str, start: datetime.date, end: datetime.date,
               as_of_time: datetime.datetime) -> pd.DataFrame:
        # short circuit if symbol missing
        if symbol not in self.df.index.get_level_values('symbol'):
            return pd.DataFrame()

        # find all dates in range where as_of_time is between start_time and end_time
        symbol_data = self.df.loc[symbol]
        mask = (symbol_data.index.get_level_values('date') >= pd.to_datetime(start)) \
            & (symbol_data.index.get_level_values('date') <= pd.to_datetime(end)) \
            & (symbol_data['start_time'] <= as_of_time) \
            & (symbol_data['end_time'] >= as_of_time)
        selected = self.df.loc[symbol][mask]
        return selected

    def insert(self, symbol: str, as_at_date: datetime.date, create_write_path_func) -> Path:
        # if there's at least one entry in the index for this (symbol, as_at_date)
        # increment the version and set the start/end times such that the previous
        # version is logically deleted and the next version becomes latest
        idx = pd.IndexSlice
        self.df.sort_index(inplace=True)
        try:
            all_versions = self.df.loc[idx[symbol, as_at_date, :]]
        except KeyError:
            all_versions = pd.DataFrame()

        if all_versions.any().any():
            start_time = datetime.datetime.utcnow()
            end_time = BiTimestamp.latest_as_of

            # this bit of awfulness is because sometimes self.df.loc[] returns
            # a scalar and sometimes it returns a Tuple; I have no idea how to
            # make it always return one or the other.
            prev_version_ndx = all_versions.index.values[-1]
            if isinstance(prev_version_ndx, Tuple):
                prev_version = prev_version_ndx[2]
            else:
                prev_version = prev_version_ndx
            version = prev_version + 1
            self.df.loc[idx[symbol, pd.to_datetime(as_at_date), prev_version], 'end_time'] = start_time
        else:
            start_time = BiTimestamp.start_as_of
            end_time = BiTimestamp.latest_as_of
            version = 0

        write_path = create_write_path_func(version)

        path = str(write_path)
        self.df.loc[idx[symbol, pd.to_datetime(as_at_date), version], ['start_time', 'end_time', 'path']] = \
            [start_time, end_time, path]

        # dirty the index
        self._mark_dirty(True)

        return write_path

    def delete(self, symbol: str, as_at_date: datetime.date):
        idx = pd.IndexSlice
        self.df.sort_index(inplace=True)
        try:
            all_versions = self.df.loc[idx[symbol, as_at_date, :]]
        except KeyError:
            all_versions = pd.DataFrame()

        if all_versions.any().any():
            start_time = datetime.datetime.utcnow()

            # see note above in insert()
            prev_version_ndx = all_versions.index.values[-1]
            if isinstance(prev_version_ndx, Tuple):
                prev_version = prev_version_ndx[2]
            else:
                prev_version = prev_version_ndx
            self.df.loc[idx[symbol, as_at_date, prev_version], 'end_time'] = start_time

            # dirty the index
            self._mark_dirty(True)

    def reindex(self):
        self.index_path.unlink()
        self._build_index()

    def flush(self):
        if self.dirty:
            self.logger.info(f'flushing index to {self.index_path}')
            self.df.to_hdf(str(self.index_path), self.table_name, mode='w', append=False, complevel=9, complib='blosc')
            self._mark_dirty(False)

    def _build_index(self):
        # initialize index; for backward compatibility support generating an index
        # from directories and files only. in this mode we also rewrite the paths
        # to support the bitemporal storage engine.
        index_rows = []
        tmp_path_index = defaultdict(list)
        splay_paths = list(self.base_path.rglob("*.h5"))
        splay_paths.sort()
        for path in splay_paths:
            # extract date
            parts = path.parts
            year = int(parts[-4])
            month = int(parts[-3])
            day = int(parts[-2])
            splay_date = datetime.date(year, month, day)

            # extract symbol
            filename = parts[-1]
            symbol_search = re.search(r'(.*?)_(\d+)\.h5', filename)
            if symbol_search:
                symbol = symbol_search.group(1)
                symbol_version = int(symbol_search.group(2))
            else:
                raise IOError(f'{filename} does not match $SYMBOL_$VERSION.h5')

            # for portability use mtime as ctime is not reliably mapped to creation time on UNIX
            last_mod_time = datetime.datetime.utcfromtimestamp(os.path.getmtime(str(path)))

            tmp_path_index[(symbol, splay_date)].append((symbol_version, str(path), last_mod_time))

        for (symbol, splay_date), versions in tmp_path_index.items():
            for ndx, version_entry in enumerate(versions):
                symbol_version = version_entry[0]
                path = version_entry[1]
                last_mod_time = version_entry[2]

                # the very first version starts at start of time, while every other
                # version starts when the version was created (last modified); we are
                # assuming here that versions are immutable, so all bets are off if
                # you go back in time and edit a version
                if ndx == 0:
                    start_time = BiTimestamp.start_as_of
                else:
                    start_time = last_mod_time

                # the very last version ends at end of time, while every other version
                # ends when the next version starts
                if ndx == (len(versions) - 1):
                    end_time = BiTimestamp.latest_as_of
                else:
                    end_time = versions[ndx + 1][2]

                # create the row for the DataFrame in dict format so we can
                # efficiently build the DataFrame all at once
                index_rows.append({'symbol': symbol,
                                   'date': splay_date,
                                   'start_time': start_time,
                                   'end_time': end_time,
                                   'version': symbol_version,
                                   'path': path
                                   })

        # build a DataFrame with multi-level index and then save to compressed HDF5. since we will
        # need to build the index after first rows inserted also capture whether it's an empty index.
        if len(index_rows) > 0:
            index_df = pd.DataFrame(index_rows)
        else:
            index_df = pd.DataFrame(columns=['symbol',
                                             'date',
                                             'start_time',
                                             'end_time',
                                             'version',
                                             'path'])

        index_df.set_index(['symbol', 'date', 'version'], inplace=True)
        self.df = index_df

        self._mark_dirty()
        self.flush()

    def _mark_dirty(self, dirty=True):
        self.dirty = dirty

    def __del__(self):
        self.flush()


class LocalTickstore(Tickstore):
    """
    Tickstore meant to run against local disk for maximum performance.
    """

    logger = logging.getLogger(__name__)

    def __init__(self, base_path: Path, timestamp_column: str = 'date'):
        self.base_path = base_path.resolve()
        self.timestamp_column = timestamp_column

        # initialize storage location
        self.base_path.mkdir(parents=True, exist_ok=True)

        # initialize and potentially build the index
        # extract table name
        table_name = self.base_path.parts[-1]
        self.index = DataFrameIndex(base_path, base_path.joinpath(Path('index.h5')), table_name)

        # initialize state
        self.closed = False

    def select(self, symbol: str, start: datetime.datetime, end: datetime.datetime,
               as_of_time: datetime.datetime = BiTimestamp.latest_as_of) -> pd.DataFrame:
        self._check_closed('select')

        # pass 1: grab the list of splays matching the start / end range that are valid for as_of_time
        selected = self.index.select(symbol, start.date(), end.date(), as_of_time)
        if selected.empty:
            return selected

        # load all ticks in range into memory
        loaded_dfs = []
        for index, row in selected.iterrows():
            loaded_dfs.append(pd.read_hdf(row['path']))

        # pass 2: select ticks matching the exact start/end timestamps
        # noinspection PyTypeChecker
        all_ticks = pd.concat(loaded_dfs)
        time_mask = (all_ticks.index.get_level_values(self.timestamp_column) >= start) \
            & (all_ticks.index.get_level_values(self.timestamp_column) <= end)

        # sort the ticks -- probably need to optimize this to sort on paths and sort ticks on ingest
        selected_ticks = all_ticks.loc[time_mask]
        selected_ticks.sort_index(inplace=True)
        return selected_ticks

    def insert(self, symbol: str, ts: BiTimestamp, ticks: pd.DataFrame):
        self._check_closed('insert')
        as_at_date = ts.as_at()

        # compose a splay path based on YYYY/MM/DD, symbol and version and pass in as a functor
        # so it can be populated with the bitemporal version
        def create_write_path(version: int):
            path = f'{as_at_date.year}/{as_at_date.month:02d}/{as_at_date.day:02d}/{symbol}_{version:04d}.h5'
            full_path = self.base_path.joinpath(path)
            self.logger.info(f'writing new data file to {full_path}')
            return full_path

        write_path = self.index.insert(symbol, as_at_date, create_write_path)

        # do the tick write, with blosc compression
        write_path.parent.mkdir(parents=True, exist_ok=True)
        ticks.to_hdf(str(write_path), 'ticks', mode='w', append=False, complevel=9, complib='blosc')

    def reindex(self):
        self.index.reindex()

    def delete(self, symbol: str, ts: BiTimestamp):
        self._check_closed('delete')
        self.index.delete(symbol, ts.as_at_date)

    def destroy(self):
        if self.base_path.exists():
            shutil.rmtree(self.base_path)

    def flush(self):
        self.index.flush()

    def close(self):
        if not self.closed:
            self.index.flush()
            self.closed = True

    def _check_closed(self, operation):
        if self.closed:
            raise Exception('unable to perform operation while closed: ' + operation)


class AzureBlobTickstore(Tickstore):
    """
    Tickstore meant to run against Microsoft's Azure Blob Storage backend, e.g. for archiving purposes. Note this is
    not suitable for concurrent access to the blob because the index is loaded into memory on the local node and only
    written back to the blob on close. We may want to implement blob locking to at least prevent accidents.
    """

    def select(self, symbol: str, start: datetime.datetime, end: datetime.datetime,
               as_of_time: datetime.datetime = BiTimestamp.latest_as_of) -> pd.DataFrame:
        raise NotImplementedError

    def insert(self, symbol: str, ts: BiTimestamp, ticks: pd.DataFrame):
        raise NotImplementedError

    def delete(self, symbol: str, ts: BiTimestamp):
        raise NotImplementedError

    def flush(self):
        pass

    def close(self):
        pass

    def destroy(self):
        pass
