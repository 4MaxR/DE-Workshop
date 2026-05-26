#!/usr/bin/env python
# coding: utf-8

"""
Ingest yellow taxi trip data (CSV.gz) from the NYC TLC repository into a PostgreSQL table.
The script processes the data in chunks to handle large files efficiently.
"""

import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm
import sys

# ==========================
#  CONFIGURATION
# ==========================
PG_USER = 'root'
PG_PASS = 'root'
PG_HOST = 'localhost'
PG_PORT = 5432
PG_DB = 'ny_taxi'

YEAR = 2021
MONTH = 1
CHUNKSIZE = 100000

target_table = 'yellow_taxi_data'

# Data types for each column (using Int64 for nullable integers)
DTYPES = {
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

PARSE_DATES = ["tpep_pickup_datetime", "tpep_dropoff_datetime"]


def main():
    """Main ingestion workflow."""
    # 1. Build the URL for the data file
    base_url = "https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow"
    url = f"{base_url}/yellow_tripdata_{YEAR}-{MONTH:02d}.csv.gz"
    print(f"📥 Reading data from: {url}")

    # 2. Create database engine
    engine = create_engine(
        f"postgresql+psycopg://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    )
    print("✅ Database engine created.")

    # 3. Set up CSV reader in chunks (iterator)
    try:
        df_iter = pd.read_csv(
            url,
            dtype=DTYPES,
            parse_dates=PARSE_DATES,
            iterator=True,
            chunksize=CHUNKSIZE,
            compression="gzip",          # explicitly handle .gz files
        )
    except Exception as e:
        print(f"❌ Failed to read CSV: {e}")
        sys.exit(1)

    # 4. Process first chunk: create table with schema
    first_chunk = next(df_iter)
    first_chunk.to_sql(
        name= target_table,
        con=engine,
        if_exists="replace",    # overwrite any existing table
        index=False,
    )
    print(f"✅ Table '{target_table}' created. First chunk inserted ({len(first_chunk)} rows).")

    # 5. Process remaining chunks with progress bar
    total_rows = len(first_chunk)
    with tqdm(total=0, desc="Inserting chunks", unit="chunk") as pbar:
        pbar.update(1)          # first chunk already done
        for chunk in df_iter:
            chunk.to_sql(
                name= target_table,
                con=engine,
                if_exists="append",
                index=False,
            )
            total_rows += len(chunk)
            pbar.update(1)
            pbar.set_postfix({"total rows": total_rows})

    print(f"\n🎉 Ingestion completed. Total rows inserted: {total_rows}")


if __name__ == "__main__":
    main()