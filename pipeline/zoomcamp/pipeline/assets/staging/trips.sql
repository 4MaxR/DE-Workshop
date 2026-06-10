/* @bruin
name: staging.trips
type: duckdb.sql

depends:
  - ingestion.trips
  - ingestion.payment_lookup

materialization:
  type: table
  strategy: time_interval
  incremental_key: pickup_datetime
  time_granularity: timestamp

columns:
  - name: pickup_datetime
    type: timestamp
    primary_key: true
    checks:
      - name: not_null
  - name: dropoff_datetime
    type: timestamp
    checks:
      - name: not_null
  - name: pickup_location_id
    type: integer
  - name: dropoff_location_id
    type: integer
  - name: taxi_type
    type: varchar
  - name: passenger_count
    type: integer
  - name: trip_distance
    type: double
  - name: payment_type
    type: integer
  - name: payment_type_name
    type: varchar
  - name: fare_amount
    type: double
    checks:
      - name: non_negative
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
  - name: extracted_at
    type: timestamp

custom_checks:
  - name: row_count_greater_than_zero
    query: |
      SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END
      FROM staging.trips
    value: 1
@bruin */

WITH deduplicated AS (
    SELECT
        tpep_pickup_datetime AS pickup_datetime,
        tpep_dropoff_datetime AS dropoff_datetime,
        pu_location_id AS pickup_location_id,
        do_location_id AS dropoff_location_id,
        taxi_type,
        passenger_count,
        trip_distance,
        payment_type,
        fare_amount,
        extra,
        mta_tax,
        tip_amount,
        tolls_amount,
        improvement_surcharge,
        total_amount,
        extracted_at,
        ROW_NUMBER() OVER (
            PARTITION BY tpep_pickup_datetime, tpep_dropoff_datetime,
                        pu_location_id, do_location_id,
                        fare_amount, taxi_type
            ORDER BY tpep_pickup_datetime
        ) AS row_num
    FROM ingestion.trips
    WHERE tpep_pickup_datetime >= '{{ start_datetime }}'
      AND tpep_pickup_datetime < '{{ end_datetime }}'
)

SELECT
    d.pickup_datetime,
    d.dropoff_datetime,
    d.pickup_location_id,
    d.dropoff_location_id,
    d.taxi_type,
    d.passenger_count,
    d.trip_distance,
    d.payment_type,
    COALESCE(p.payment_type_name, 'unknown') AS payment_type_name,
    d.fare_amount,
    d.extra,
    d.mta_tax,
    d.tip_amount,
    d.tolls_amount,
    d.improvement_surcharge,
    d.total_amount,
    d.extracted_at
FROM deduplicated d
LEFT JOIN ingestion.payment_lookup p
    ON d.payment_type = p.payment_type_id
WHERE d.row_num = 1
AND d.fare_amount >= 0