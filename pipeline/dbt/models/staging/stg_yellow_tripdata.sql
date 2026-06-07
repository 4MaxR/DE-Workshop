SELECT 
    -- identifiers
    CAST(VendorID AS INT64) AS vendor_id,
    CAST(RatecodeID AS INT64) AS rate_code_id,
    CAST(PULocationID AS INT64) AS pickup_location_id,
    CAST(DOLocationID AS INT64) AS dropoff_location_id,

    -- timestamps
    CAST(tpep_pickup_datetime AS TIMESTAMP) AS pickup_datetime,
    CAST(tpep_dropoff_datetime AS TIMESTAMP) AS dropoff_datetime,

    -- trip info
    CAST(store_and_fwd_flag AS STRING) AS store_and_fwd_flag,
    CAST(passenger_count AS INT64) AS passenger_count,
    CAST(trip_distance AS FLOAT64) AS trip_distance,
    1 AS trip_type, -- yellow taxis can only be street-hail (trip_type = 1) same value from green taxi

    -- payment info (all NUMERIC for precise money values)
    CAST(fare_amount AS NUMERIC) AS fare_amount,
    CAST(extra AS NUMERIC) AS extra,
    CAST(mta_tax AS NUMERIC) AS mta_tax,
    CAST(tip_amount AS NUMERIC) AS tip_amount,
    CAST(tolls_amount AS NUMERIC) AS tolls_amount,
    0 AS ehail_fee, -- yellow taxi doesn't have ehail fee 
    CAST(improvement_surcharge AS NUMERIC) AS improvement_surcharge,
    CAST(total_amount AS NUMERIC) AS total_amount,
    CAST(payment_type AS INT64) AS payment_type,

FROM {{ source('raw_data', 'yellow_tripdata_partitioned') }}
WHERE VendorID IS NOT NULL 
    -- Remove invalid trips with non-positive distance
AND trip_distance > 0