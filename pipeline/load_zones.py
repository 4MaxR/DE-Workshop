#!/usr/bin/env python
# coding: utf-8

"""
Load the taxi zone lookup table from NYC TLC into PostgreSQL.
"""

import click
import pandas as pd
from sqlalchemy import create_engine, text
import sys

@click.command()
@click.option('--pg-user', default='root', help='PostgreSQL user')
@click.option('--pg-pass', default='root', help='PostgreSQL password')
@click.option('--pg-host', default='localhost', help='PostgreSQL host')
@click.option('--pg-port', default=5432, type=int, help='PostgreSQL port')
@click.option('--pg-db', default='ny_taxi', help='PostgreSQL database name')
@click.option('--target-table', default='zones', help='Target table name')
@click.option('--url', default='https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv',
            help='URL of the taxi zone lookup CSV')
def main(pg_user, pg_pass, pg_host, pg_port, pg_db, target_table, url):
    """Load taxi zone lookup table into PostgreSQL."""
    
    click.echo(f"📥 Downloading zone lookup from:\n  {url}")
    
    # Create database engine
    try:
        engine = create_engine(
            f"postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        click.echo("✅ Database connected.")
    except Exception as e:
        click.echo(f"❌ Database connection failed: {e}", err=True)
        sys.exit(1)
    
    # Read CSV directly from URL
    try:
        df = pd.read_csv(url)
        click.echo(f"✅ Downloaded {len(df)} rows.")
    except Exception as e:
        click.echo(f"❌ Failed to read CSV: {e}", err=True)
        sys.exit(1)
    
    # Write to PostgreSQL (replace any existing table)
    try:
        df.to_sql(
            name=target_table,
            con=engine,
            if_exists='replace',
            index=False
        )
        click.echo(f"✅ Table '{target_table}' created with {len(df)} rows.")
    except Exception as e:
        click.echo(f"❌ Failed to write to database: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()