"""@bruin

name: ingestion.trips
connection: duckdb-default

materialization:
  type: table
  strategy: append

image: python:3.11

columns:
  - name: vendor_id
    type: integer
  - name: tpep_pickup_datetime
    type: timestamp
  - name: tpep_dropoff_datetime
    type: timestamp
  - name: passenger_count
    type: integer
  - name: trip_distance
    type: double
  - name: pu_location_id
    type: integer
  - name: do_location_id
    type: integer
  - name: payment_type
    type: integer
  - name: fare_amount
    type: double
  - name: extra
    type: double
  - name: mta_tax
    type: double
  - name: tip_amount
    type: double
  - name: tolls_amount
    type: double
  - name: improvement_surcharge
    type: double
  - name: total_amount
    type: double
  - name: taxi_type
    type: varchar
  - name: extracted_at
    type: timestamp

@bruin"""

import pandas as pd
import os
from datetime import datetime
import requests
from io import BytesIO
import json

def materialize():
    # Read parameters from environment variables (set by Bruin)
    params_str = os.environ.get('BRUIN_PARAMS', '{}')
    params = json.loads(params_str)
    
    taxi_types = params.get("taxi_types", ["yellow", "green"])
    year = params.get("year", 2023)
    month = params.get("month", 1)

    base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/"
    all_dfs = []

    for taxi_type in taxi_types:
        file_name = f"{taxi_type}_tripdata_{year}-{month:02d}.parquet"
        url = base_url + file_name

        print(f"Fetching {url}...")
        response = requests.get(url)
        response.raise_for_status()

        df = pd.read_parquet(BytesIO(response.content))

        # Rename location columns to snake_case
        df = df.rename(columns={
            'PULocationID': 'pu_location_id',
            'DOLocationID': 'do_location_id'
        })

        # Add taxi_type column
        df['taxi_type'] = taxi_type

        # Add extraction timestamp
        df['extracted_at'] = datetime.utcnow()

        all_dfs.append(df)

    if not all_dfs:
        raise ValueError("No data fetched")

    result = pd.concat(all_dfs, ignore_index=True)

    # Ensure column order matches the defined columns
    # (optional, but good practice)
    column_names = [
        'vendor_id', 'tpep_pickup_datetime', 'tpep_dropoff_datetime',
        'passenger_count', 'trip_distance', 'pu_location_id', 'do_location_id',
        'payment_type', 'fare_amount', 'extra', 'mta_tax', 'tip_amount',
        'tolls_amount', 'improvement_surcharge', 'total_amount',
        'taxi_type', 'extracted_at'
    ]
    # Only keep columns that exist in the DataFrame
    existing_cols = [c for c in column_names if c in result.columns]
    result = result[existing_cols]

    return result