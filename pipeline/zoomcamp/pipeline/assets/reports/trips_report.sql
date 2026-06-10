/* @bruin

# Reports: daily trip metrics by taxi type
name: reports.trips_report
type: duckdb.sql

depends:
  - staging.trips

materialization:
  type: table
  strategy: time_interval
  incremental_key: pickup_date
  time_granularity: date

columns:
  - name: pickup_date
    type: date
    description: Date of trip pickup
    primary_key: true
    checks:
      - name: not_null
  - name: taxi_type
    type: varchar
    description: Yellow, Green, etc.
    primary_key: true
  - name: total_trips
    type: bigint
    description: Number of trips on that day per taxi type
    checks:
      - name: non_negative
  - name: total_fare_amount
    type: double
    description: Sum of fare_amount
    checks:
      - name: non_negative
  - name: avg_fare_amount
    type: double
    description: Average fare per trip
  - name: total_tip_amount
    type: double
    description: Sum of tips
    checks:
      - name: non_negative
  - name: avg_tip_amount
    type: double
    description: Average tip per trip
  - name: total_trip_distance
    type: double
    description: Total distance travelled
  - name: avg_trip_distance
    type: double
    description: Average distance per trip

custom_checks:
  - name: total_trips_positive
    query: |
      SELECT CASE WHEN MIN(total_trips) > 0 THEN 1 ELSE 0 END
      FROM reports.trips_report
    value: 1

@bruin */

WITH daily_agg AS (
    SELECT
        DATE(pickup_datetime) AS pickup_date,
        taxi_type,
        COUNT(*) AS total_trips,
        SUM(fare_amount) AS total_fare_amount,
        AVG(fare_amount) AS avg_fare_amount,
        SUM(tip_amount) AS total_tip_amount,
        AVG(tip_amount) AS avg_tip_amount,
        SUM(trip_distance) AS total_trip_distance,
        AVG(trip_distance) AS avg_trip_distance
    FROM staging.trips
    WHERE pickup_datetime >= '{{ start_datetime }}'
      AND pickup_datetime < '{{ end_datetime }}'
    GROUP BY DATE(pickup_datetime), taxi_type
)

SELECT
    pickup_date,
    taxi_type,
    total_trips,
    total_fare_amount,
    avg_fare_amount,
    total_tip_amount,
    avg_tip_amount,
    total_trip_distance,
    avg_trip_distance
FROM daily_agg
ORDER BY pickup_date, taxi_type