#!/usr/bin/env python
# coding: utf-8

"""
Ingest yellow taxi trip data (CSV.gz) from the NYC TLC repository into a PostgreSQL table.
The script processes the data in chunks to handle large files efficiently.
"""

import click
import pandas as pd
from sqlalchemy import create_engine, text
from tqdm.auto import tqdm
import sys

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


@click.command()
@click.option('--pg-user', default='root', help='PostgreSQL user')
@click.option('--pg-pass', default='root', help='PostgreSQL password', hide_input=False)
@click.option('--pg-host', default='localhost', help='PostgreSQL host')
@click.option('--pg-port', default=5432, type=int, help='PostgreSQL port')
@click.option('--pg-db', default='ny_taxi', help='PostgreSQL database name')
@click.option('--year', default=2021, type=int, help='Year of the data (YYYY)')
@click.option('--month', default=1, type=click.IntRange(1, 12), help='Month of the data (1-12)')
@click.option('--target-table', default='yellow_taxi_data', help='Target table name')
@click.option('--chunksize', default=100000, type=int, help='Rows per chunk')
@click.option('--base-url', default='https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow',
            help='Base URL for the taxi data files')
def main(pg_user, pg_pass, pg_host, pg_port, pg_db, year, month, target_table, chunksize, base_url):
    """Ingest NYC yellow taxi data into a PostgreSQL database."""

    # Build the URL for the specific year/month file
    url = f"{base_url}/yellow_tripdata_{year}-{month:02d}.csv.gz"
    click.echo(f"📥 Reading data from: {url}")

    # Create database engine
    try:
        engine = create_engine(
            f"postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
        )
        # Test the connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        click.echo("✅ Database engine created and connected.")
    except Exception as e:
        click.echo(f"❌ Failed to connect to database: {e}", err=True)
        sys.exit(1)

    # Set up CSV reader in chunks (iterator)
    try:
        df_iter = pd.read_csv(
            url,
            dtype=DTYPES,
            parse_dates=PARSE_DATES,
            iterator=True,
            chunksize=chunksize,
            compression="gzip",
        )
    except Exception as e:
        click.echo(f"❌ Failed to read CSV from URL: {e}", err=True)
        sys.exit(1)

    # Process first chunk: create table with schema and data
    try:
        first_chunk = next(df_iter)
    except StopIteration:
        click.echo("❌ No data found in the file.", err=True)
        sys.exit(1)

    first_chunk.to_sql(
        name=target_table,
        con=engine,
        if_exists="replace",
        index=False,
    )
    total_rows = len(first_chunk)
    click.echo(
        f"✅ Table '{target_table}' created. First chunk inserted ({total_rows} rows).")

    # Process remaining chunks with progress bar
    total_rows = 0
    for chunk in tqdm(df_iter, desc="Inserting chunks", unit="chunk"):
        chunk.to_sql(name=target_table, con=engine, if_exists='append', index=False)
        total_rows += len(chunk)
    click.echo(f"\n🎉 Total rows inserted: {total_rows}")


if __name__ == "__main__":
    main()
