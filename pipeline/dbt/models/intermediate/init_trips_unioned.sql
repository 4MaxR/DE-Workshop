WITH green_tripdata AS (
    SELECT * FROM {{ ref('stg_green_tripdata') }}
),

yellow_tripdata AS (
    SELECT * FROM {{ ref('stg_yellow_tripdata') }}
),

trips_unioned AS (
    SELECT * FROM green_tripdata

    UNION ALL

    SELECT * FROM yellow_tripdata
),

deduplicated AS (

    SELECT *
    FROM (

        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY
                    vendor_id,
                    pickup_datetime,
                    dropoff_datetime,
                    pickup_location_id,
                    dropoff_location_id,
                    CAST(trip_distance AS NUMERIC),
                    fare_amount,
                    total_amount,
                    payment_type
                ORDER BY pickup_datetime, dropoff_datetime
            ) AS rn

        FROM trips_unioned

    )

    WHERE rn = 1

)

SELECT * EXCEPT(rn)
FROM deduplicated