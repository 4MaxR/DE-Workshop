#!/usr/bin/env python
# coding: utf-8


import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm


def run():
    pg_user = 'root'
    pg_pass = 'root'
    pg_host = 'localhost'
    pg_port = 5432
    pg_db = 'ny_taxi'

    year = 2021
    month = 1

    chunksize = 100000

    df_iter = pd.read_csv(
        url,
        dtype=dtype,
        parse_dates=parse_dates,
        iterator=True,
        chunksize=chunksize,
    )


dtype = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64"
}

parse_dates = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime"
]

df = pd.read_csv(
    url,
    dtype=dtype,
    parse_dates=parse_dates
)


df = pd.read_csv(url)


df.head()


df['VendorID']


len(df)


get_ipython().system('uv add sqlalchemy "psycopg[binary,pool]"')


prefix = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow'
url = f'{prefix}/yellow_tripdata_{year}-{month:02d}.csv.gz'

engine = create_engine(
    f'postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}')


df.head(n=0).to_sql(name='yellow_taxi_data', con=engine, if_exists='replace')


print(pd.io.sql.get_schema(df, name='yellow_taxi_data', con=engine))


df = next(df_iter)


for df in df_iter:
    print(len(df))


for df_chunk in tqdm(df_iter):
    df_chunk.to_sql(
        name='yellow_taxi_data',
        con=engine,
        if_exists='append'
    )


get_ipython().system('uv add tqdm')


for df_chunk in tqdm(df_iter):
    df_chunk.to_sql(name='yellow_texi_data', con=engine, if_exists='append')


engine


engine.connect()


for df_chunk in df_iter:
    print("Chunk received")
    break


small_df = df.head(1000)

small_df.to_sql(
    name='yellow_taxi_data',
    con=engine,
    if_exists='append'
)


get_ipython().system('dir')
