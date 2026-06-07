-- In dim_locations.sql
with taxi_zone_lookup as (
    select * from `datatalkclub-498309.zoomcamp.taxi_zone_lookup`
),
renamed as (
    select
        locationid as location_id,
        borough,
        zone,
        service_zone
    from taxi_zone_lookup
)
select * from renamed