import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def generate_and_random_ticks(
        ts_col_name='ts',
        start=pd.to_datetime('2019-10-1'),
        end=pd.to_datetime('2019-10-31'),
        col_list=list('ABCDEFGH'),
        file_path='tick_testdata.parquet'):
    writer = None
    try:
        for i in range(31):
            ts_index = random_dates(start, end, 100)
            ts_index.name = ts_col_name
            ticks = pd.DataFrame(np.random.randint(0, 100, size=(100, len(col_list))), columns=col_list, index=ts_index)
            writer = append_to_parquet(ticks, writer, file_path)
    finally:
        writer.close()

    in_pd = pq.read_table(file_path).to_pandas()
    print(in_pd)


def append_to_parquet(
        df: pd.DataFrame,
        writer: pq.ParquetWriter,
        file_path: str) -> pq.ParquetWriter:
    table = pa.Table.from_pandas(df)
    if writer is None:
        writer = pq.ParquetWriter(file_path, table.schema)
    writer.write_table(table=table)
    return writer


def random_dates(start, end, n):
    start_u = start.value // 10 ** 9
    end_u = end.value // 10 ** 9
    return pd.to_datetime(np.random.randint(start_u, end_u, n), unit='s')


if __name__ == "__main__":
    generate_and_random_ticks()
