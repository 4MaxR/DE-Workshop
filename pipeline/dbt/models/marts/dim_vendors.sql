WITH trips_unioned AS (
    select * FROM {{ ref('init_trips_unioned')}}
),

vendors as (
    select 
        distinct vendor_id,
    {{ get_vendor_names('vendor_id')}} as vendor_name
    FROM trips_unioned
)

SELECT * FROM vendors