with trips as (

    select
        vendor_id,
        rate_code_id,
        pickup_location_id,
        dropoff_location_id,
        pickup_datetime,
        dropoff_datetime,

        case
            when cast(store_and_fwd_flag as string) in ('false', 'N') then 'N'
            when cast(store_and_fwd_flag as string) in ('true', 'Y') then 'Y'
            else cast(store_and_fwd_flag as string)
        end as store_and_fwd_flag,

        passenger_count,
        trip_distance,
        trip_type,
        fare_amount,
        extra,
        mta_tax,
        tip_amount,
        {{ get_payment_type_name('payment_type')}} as payment_type,
        tolls_amount,
        coalesce(ehail_fee, 0) as ehail_fee,

        improvement_surcharge,
        total_amount

    from {{ ref('init_trips_unioned') }}

)

select

{{ dbt_utils.generate_surrogate_key([
    'vendor_id',
    'pickup_datetime',
    'dropoff_datetime',
    'pickup_location_id',
    'dropoff_location_id',
    'trip_distance',
    'fare_amount',
    'total_amount',
    'payment_type'
]) }} as trip_id,

    *

from trips