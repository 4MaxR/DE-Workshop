{% macro get_payment_type_name(payment_type_column) %}
    CASE 
        WHEN {{ payment_type_column }} = 1 THEN 'Credit Card'
        WHEN {{ payment_type_column }} = 2 THEN 'Cash'
        WHEN {{ payment_type_column }} = 3 THEN 'No Charge'
        WHEN {{ payment_type_column }} = 4 THEN 'Dispute'
        WHEN {{ payment_type_column }} = 5 THEN 'Unknown'
        ELSE 'Other'
    END
{% endmacro %}