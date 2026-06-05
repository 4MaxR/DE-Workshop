-- Query public available table
SELECT
    station_id,
    name
FROM bigquery-public-data.new_york_citibike.citibike_stations
LIMIT 100;

-- Create an external table referencing files in GCS
CREATE OR REPLACE EXTERNAL TABLE `datatalkclub-498309.zoomcamp.external_yellow_tripdata`
OPTIONS (
    format = 'CSV',
    uris = [
        'gs://mustafa-data-lake-123456/yellow_tripdata_2019-*.csv',
        'gs://mustafa-data-lake-123456/yellow_tripdata_2020-*.csv'
    ]
);

-- Preview yellow trip data from the external table
SELECT *
FROM `datatalkclub-498309.zoomcamp.external_yellow_tripdata`
LIMIT 10;

-- Create a non-partitioned table from the external table
CREATE OR REPLACE TABLE datatalkclub-498309.zoomcamp.yellow_tripdata_non_partitioned AS
SELECT *
FROM `datatalkclub-498309.zoomcamp.external_yellow_tripdata`;

-- Create a partitioned table from the external table
CREATE OR REPLACE TABLE datatalkclub-498309.zoomcamp.yellow_tripdata_partitioned
PARTITION BY DATE(tpep_pickup_datetime) AS
SELECT *
FROM datatalkclub-498309.zoomcamp.external_yellow_tripdata;

# Check partitioned
SELECT
  MIN(DATE(tpep_pickup_datetime)) AS min_date,
  MAX(DATE(tpep_pickup_datetime)) AS max_date,
  COUNT(DISTINCT DATE(tpep_pickup_datetime)) AS num_days
FROM `datatalkclub-498309.zoomcamp.yellow_tripdata_partitioned`;

SELECT
    MIN(tpep_pickup_datetime) AS min_ts,
    MAX(tpep_pickup_datetime) AS max_ts
FROM `datatalkclub-498309.zoomcamp.external_yellow_tripdata`;

SELECT
    tpep_pickup_datetime
FROM `datatalkclub-498309.zoomcamp.yellow_tripdata_partitioned`
WHERE EXTRACT(YEAR FROM tpep_pickup_datetime) NOT BETWEEN 2018 AND 2021
LIMIT 20;

SELECT
    tpep_pickup_datetime
FROM `datatalkclub-498309.zoomcamp.external_yellow_tripdata`
LIMIT 10;

SELECT COUNT(*)
FROM `datatalkclub-498309.zoomcamp.yellow_tripdata_non_partitioned`
WHERE DATE(tpep_pickup_datetime) = '2019-01-15';

SELECT COUNT(*)
FROM `datatalkclub-498309.zoomcamp.yellow_tripdata_partitioned`
WHERE DATE(tpep_pickup_datetime) = '2019-01-15';

-- Impact of partition
-- Scanning 1.6GB of data
SELECT DISTINCT(VendorID)
FROM datatalkclub-498309.zoomcamp.yellow_tripdata_non_partitioned
WHERE DATE(tpep_pickup_datetime) BETWEEN '2019-06-01' AND '2019-06-30';

-- Scanning ~106 MB of DATA
SELECT DISTINCT(VendorID)
FROM taxi-rides-ny.nytaxi.yellow_tripdata_partitioned
WHERE DATE(tpep_pickup_datetime) BETWEEN '2019-06-01' AND '2019-06-30';

-- Inspect table partitions
SELECT
    table_name,
    partition_id,
    total_rows
FROM `nytaxi.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name = 'yellow_tripdata_partitioned'
ORDER BY total_rows DESC;

-- Creating a partition and cluster table
CREATE OR REPLACE TABLE datatalkclub-498309.zoomcamp.yellow_tripdata_partitioned_clustered
PARTITION BY DATE(tpep_pickup_datetime)
CLUSTER BY VendorID AS
SELECT * 
FROM datatalkclub-498309.zoomcamp.external_yellow_tripdata;

-- Query scans 1.1 GB
SELECT count(*) as trips
FROM datatalkclub-498309.zoomcamp.yellow_tripdata_partitioned
WHERE DATE(tpep_pickup_datetime) BETWEEN '2019-06-01' AND '2020-12-31'
  AND VendorID=1;

SELECT
  VendorID,
  COUNT(*) AS trips
FROM `datatalkclub-498309.zoomcamp.yellow_tripdata_partitioned`
GROUP BY VendorID
ORDER BY trips DESC;

SELECT
  MIN(tpep_pickup_datetime),
  MAX(tpep_pickup_datetime)
FROM `datatalkclub-498309.zoomcamp.yellow_tripdata_partitioned`
WHERE VendorID = 1;

SELECT
  EXTRACT(YEAR FROM tpep_pickup_datetime) AS yr,
  COUNT(*) AS trips
FROM `datatalkclub-498309.zoomcamp.yellow_tripdata_partitioned`
WHERE VendorID = 1
GROUP BY yr
ORDER BY yr;

SELECT
  EXTRACT(YEAR FROM tpep_pickup_datetime) AS yr,
  EXTRACT(MONTH FROM tpep_pickup_datetime) AS mn,
  COUNT(*) AS trips
FROM `datatalkclub-498309.zoomcamp.yellow_tripdata_partitioned`
GROUP BY yr, mn
ORDER BY yr, mn;

SELECT COUNT(*)
FROM `datatalkclub-498309.zoomcamp.external_yellow_tripdata`;

-- Query scans 864.5 MB
SELECT count(*) as trips
FROM taxi-rides-ny.nytaxi.yellow_tripdata_partitioned_clustered
WHERE DATE(tpep_pickup_datetime) BETWEEN '2019-06-01' AND '2020-12-31'
  AND VendorID=1;
