with source_events as (
    select
        parse_date('%Y%m%d', event_date) as event_date,
        event_timestamp,
        event_name,
        user_pseudo_id,
        ecommerce.transaction_id as order_id,
        ecommerce.purchase_revenue_in_usd as purchase_revenue_usd,
        ecommerce.refund_value_in_usd as refund_value_usd,
        ecommerce.shipping_value_in_usd as shipping_value_usd,
        ecommerce.tax_value_in_usd as tax_value_usd,
        ecommerce.total_item_quantity as item_quantity,
        device.category as device_category,
        geo.country as country,
        traffic_source.source as traffic_source,
        traffic_source.medium as traffic_medium,
        traffic_source.name as campaign_name
    from `{{ var('ga4_project_id') }}.{{ var('ga4_dataset') }}.events_*`
    where _table_suffix between '{{ var("start_date") }}' and '{{ var("end_date") }}'
)

select *
from source_events
