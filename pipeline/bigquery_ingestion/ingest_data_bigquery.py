#!/usr/bin/env python3
"""
taxi_pipeline.py

Replicates the Kestra workflow '08_gcp_taxi.yaml' for NYC taxi data.
Downloads CSV.GZ from GitHub, uploads to GCS, creates BigQuery external table,
builds a staging table with a unique row ID, and merges into a final partitioned table.

Environment variables (or arguments with --set-env):
    GCP_PROJECT_ID      - Google Cloud project ID
    GCP_DATASET         - BigQuery dataset name
    GCP_BUCKET_NAME     - GCS bucket name
    GCP_LOCATION        - GCS/BQ location (default: 'US')

Usage:
    python taxi_pipeline.py --taxi green --year 2020 --month 01
    python taxi_pipeline.py --taxi yellow --year 2019 --month 12 --purge-intermediate
"""

from google.cloud.exceptions import NotFound
from google.cloud import bigquery, storage
import requests
import argparse
import gzip
import hashlib
import logging
import os
import sys
from urllib.request import urlopen
from dotenv import load_dotenv
load_dotenv()  # This loads from .env file


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_config():
    """Retrieve configuration from environment variables."""
    required = ["GCP_PROJECT_ID", "GCP_DATASET", "GCP_BUCKET_NAME"]
    config = {}
    missing = []
    for var in required:
        val = os.environ.get(var)
        if not val:
            missing.append(var)
        config[var] = val
    config["GCP_LOCATION"] = os.environ.get("GCP_LOCATION", "EU")
    if missing:
        logger.error(
            f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
    return config


def download_and_gunzip(taxi_type: str, year: str, month: str) -> bytes:
    """Download compressed CSV from GitHub, decompress, return bytes."""
    filename = f"{taxi_type}_tripdata_{year}-{month}.csv.gz"
    url = f"https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{taxi_type}/{filename}"
    logger.info(f"Downloading {url}")
    with urlopen(url) as resp:
        content = gzip.decompress(resp.read())
    logger.info(f"Downloaded and decompressed {len(content)} bytes")
    return content


def upload_to_gcs(bucket_name: str, data: bytes, destination_blob: str) -> str:
    """Upload bytes to GCS bucket. Returns gs:// URI."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob)
    blob.upload_from_string(data, content_type="text/csv")
    gs_uri = f"gs://{bucket_name}/{destination_blob}"
    logger.info(f"Uploaded to {gs_uri}")
    return gs_uri


def create_external_table(project_id: str, dataset: str, table_name: str, gcs_uri: str, schema, skip_leading_rows=1):
    """Create or replace an external table on the CSV file."""
    client = bigquery.Client(project=project_id)
    table_id = f"{project_id}.{dataset}.{table_name}"
    external_config = bigquery.ExternalConfig("CSV")
    external_config.source_uris = [gcs_uri]
    external_config.options.skip_leading_rows = skip_leading_rows
    external_config.options.ignore_unknown_values = True
    external_config.schema = schema

    table = bigquery.Table(table_id)
    table.external_data_configuration = external_config

    client.delete_table(table_id, not_found_ok=True)
    client.create_table(table)
    logger.info(f"External table created: {table_id}")
    return table_id


def create_staging_table_from_external(project_id: str, dataset: str, staging_table_name: str,
                                       external_table_id: str, filename: str, taxi_type: str):
    """
    Create staging table with unique_row_id (MD5) and filename column.
    Detects the correct pickup/dropoff columns based on taxi_type.
    """
    client = bigquery.Client(project=project_id)
    staging_table_id = f"{project_id}.{dataset}.{staging_table_name}"

    # Determine column names for hash based on taxi type
    if taxi_type == "yellow":
        vendor_col = "VendorID"
        pickup_col = "tpep_pickup_datetime"
        dropoff_col = "tpep_dropoff_datetime"
        pu_col = "PULocationID"
        do_col = "DOLocationID"
    else:  # green
        vendor_col = "VendorID"
        pickup_col = "lpep_pickup_datetime"
        dropoff_col = "lpep_dropoff_datetime"
        pu_col = "PULocationID"
        do_col = "DOLocationID"

    hash_expr = f"""
        CAST(MD5(CONCAT(
        COALESCE(CAST({vendor_col} AS STRING), ''),
        COALESCE(CAST({pickup_col} AS STRING), ''),
        COALESCE(CAST({dropoff_col} AS STRING), ''),
        COALESCE(CAST({pu_col} AS STRING), ''),
        COALESCE(CAST({do_col} AS STRING), '')
    )) AS BYTES) AS unique_row_id
    """
    sql = f"""
        CREATE OR REPLACE TABLE `{staging_table_id}` AS
        SELECT
            {hash_expr} AS unique_row_id,
            '{filename}' AS filename,
            *
        FROM `{external_table_id}`
    """
    logger.info(f"Creating staging table {staging_table_id}")
    job = client.query(sql)
    job.result()
    logger.info("Staging table created")
    return staging_table_id


def ensure_final_table_exists(project_id: str, dataset: str, final_table_name: str, taxi_type: str):
    """Create final table if it doesn't exist, with partitioning on pickup datetime."""
    client = bigquery.Client(project=project_id)
    final_table_id = f"{project_id}.{dataset}.{final_table_name}"
    try:
        client.get_table(final_table_id)
        logger.info(f"Final table {final_table_id} already exists")
        return final_table_id
    except NotFound:
        # Determine the pickup column for partitioning
        pickup_col = "tpep_pickup_datetime" if taxi_type == "yellow" else "lpep_pickup_datetime"
        # We need a schema; we'll copy from a dummy external table? Simpler: create with minimal schema.
        # Since we will merge, we can let the first merge create the table if not exists.
        # But for partitioning to work, we need to set it upfront.
        # We'll create it with a basic schema derived from the staging table after it's built.
        # Alternative: create after staging is ready, but the merge will also work if we set partitioning later.
        # However, it's cleaner to create a placeholder and alter later. For simplicity, we let the merge create the table
        # and then add partitioning. But that's messy. Better: define schema manually.
        # Let's use a simplified approach: create the final table with only unique_row_id and filename,
        # then the merge will add columns automatically? No, BigQuery doesn't auto-add columns.
        # So we need to create the table with the full schema. We'll copy schema from staging after it's created.
        # But ensure_final_table_exists is called before staging? We'll restructure.
        # For this script, we'll call this function after staging is created and use its schema.
        # I'll adjust the flow.
        logger.info(
            f"Final table {final_table_id} does not exist; it will be created during merge.")
        return final_table_id


def merge_into_final(project_id: str, dataset: str, final_table_name: str, staging_table_id: str, taxi_type: str):
    """
    Merge staging table into final table. Creates final table if not present.
    """
    client = bigquery.Client(project=project_id)
    final_table_id = f"{project_id}.{dataset}.{final_table_name}"

    # Get staging table schema to create final table if needed
    try:
        client.get_table(final_table_id)
    except NotFound:
        staging_table = client.get_table(staging_table_id)
        # Create final table with partitioning
        pickup_col = "tpep_pickup_datetime" if taxi_type == "yellow" else "lpep_pickup_datetime"
        table = bigquery.Table(final_table_id, schema=staging_table.schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field=pickup_col
        )
        client.create_table(table)
        logger.info(
            f"Created final table {final_table_id} with partitioning on {pickup_col}")

    # Build list of columns from staging schema (excluding unique_row_id? include all)
    staging_table = client.get_table(staging_table_id)
    if staging_table.num_rows == 0:
        logger.info("Staging table has no rows. Skipping merge.")
        return
    column_names = [field.name for field in staging_table.schema]
    columns_str = ", ".join(column_names)
    insert_columns = ", ".join([f"S.{c}" for c in column_names])

    sql = f"""
        MERGE INTO `{final_table_id}` T
        USING `{staging_table_id}` S
        ON T.unique_row_id = S.unique_row_id
        WHEN NOT MATCHED THEN
            INSERT ({columns_str})
            VALUES ({insert_columns})
    """
    logger.info("Starting merge into final table")
    job = client.query(sql)
    job.result()
    logger.info("Merge completed")


def cleanup_tables(project_id: str, dataset: str, table_names: list):
    """Delete specified tables (external and staging)."""
    client = bigquery.Client(project=project_id)
    for name in table_names:
        table_id = f"{project_id}.{dataset}.{name}"
        client.delete_table(table_id, not_found_ok=True)
        logger.info(f"Deleted {table_id}")


def main():
    parser = argparse.ArgumentParser(
        description="NYC Taxi data pipeline to BigQuery")
    parser.add_argument("--taxi", required=True,
                        choices=["yellow", "green"], help="Taxi type")
    parser.add_argument("--year", required=True, help="Year (e.g., 2019)")
    parser.add_argument("--month", required=True, help="Month (01-12)")
    parser.add_argument("--purge-intermediate", action="store_true",
                        help="Delete external and staging tables after merge")
    args = parser.parse_args()

    config = get_config()
    project_id = config["GCP_PROJECT_ID"]
    dataset = config["GCP_DATASET"]
    bucket_name = config["GCP_BUCKET_NAME"]
    location = config["GCP_LOCATION"]

    # Validate month format
    if not (args.month.isdigit() and 1 <= int(args.month) <= 12):
        logger.error("Month must be 01-12")
        sys.exit(1)

    # File naming
    csv_filename = f"{args.taxi}_tripdata_{args.year}-{args.month}.csv"
    ext_table_name = csv_filename.replace(".csv", "_ext")
    staging_table_name = csv_filename.replace(".csv", "")
    final_table_name = f"{args.taxi}_tripdata"

    # Step 1: Download and decompress
    data = download_and_gunzip(args.taxi, args.year, args.month)

    # Step 2: Upload to GCS
    gcs_uri = upload_to_gcs(bucket_name, data, csv_filename)

    # Step 3: Define schema
    if args.taxi == "yellow":
        schema = [
            bigquery.SchemaField("VendorID", "STRING"),
            bigquery.SchemaField("tpep_pickup_datetime", "TIMESTAMP"),
            bigquery.SchemaField("tpep_dropoff_datetime", "TIMESTAMP"),
            bigquery.SchemaField("passenger_count", "INTEGER"),
            bigquery.SchemaField("trip_distance", "NUMERIC"),
            bigquery.SchemaField("RatecodeID", "STRING"),
            bigquery.SchemaField("store_and_fwd_flag", "STRING"),
            bigquery.SchemaField("PULocationID", "STRING"),
            bigquery.SchemaField("DOLocationID", "STRING"),
            bigquery.SchemaField("payment_type", "INTEGER"),
            bigquery.SchemaField("fare_amount", "NUMERIC"),
            bigquery.SchemaField("extra", "NUMERIC"),
            bigquery.SchemaField("mta_tax", "NUMERIC"),
            bigquery.SchemaField("tip_amount", "NUMERIC"),
            bigquery.SchemaField("tolls_amount", "NUMERIC"),
            bigquery.SchemaField("improvement_surcharge", "NUMERIC"),
            bigquery.SchemaField("total_amount", "NUMERIC"),
            bigquery.SchemaField("congestion_surcharge", "NUMERIC"),
        ]
    else:
        schema = [
            bigquery.SchemaField("VendorID", "STRING"),
            bigquery.SchemaField("lpep_pickup_datetime", "TIMESTAMP"),
            bigquery.SchemaField("lpep_dropoff_datetime", "TIMESTAMP"),
            bigquery.SchemaField("store_and_fwd_flag", "STRING"),
            bigquery.SchemaField("RatecodeID", "STRING"),
            bigquery.SchemaField("PULocationID", "STRING"),
            bigquery.SchemaField("DOLocationID", "STRING"),
            bigquery.SchemaField("passenger_count", "INTEGER"),
            bigquery.SchemaField("trip_distance", "NUMERIC"),
            bigquery.SchemaField("fare_amount", "NUMERIC"),
            bigquery.SchemaField("extra", "NUMERIC"),
            bigquery.SchemaField("mta_tax", "NUMERIC"),
            bigquery.SchemaField("tip_amount", "NUMERIC"),
            bigquery.SchemaField("tolls_amount", "NUMERIC"),
            bigquery.SchemaField("ehail_fee", "NUMERIC"),
            bigquery.SchemaField("improvement_surcharge", "NUMERIC"),
            bigquery.SchemaField("total_amount", "NUMERIC"),
            bigquery.SchemaField("payment_type", "INTEGER"),
            bigquery.SchemaField("trip_type", "STRING"),
            bigquery.SchemaField("congestion_surcharge", "NUMERIC"),
        ]

    # Step 4: Create external table
    ext_table_id = create_external_table(
        project_id, dataset, ext_table_name, gcs_uri, schema)

    # Step 5: Create staging table with unique_row_id
    staging_table_id = create_staging_table_from_external(
        project_id, dataset, staging_table_name, ext_table_id, csv_filename, args.taxi
    )

    # Step 6: Merge into final table
    merge_into_final(project_id, dataset, final_table_name,
                    staging_table_id, args.taxi)

    # Step 7: Cleanup if requested
    if args.purge_intermediate:
        cleanup_tables(project_id, dataset, [
            ext_table_name, staging_table_name])

    logger.info("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
