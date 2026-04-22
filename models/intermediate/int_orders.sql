with purchase_events as (
    select
        event_date,
        order_id,
        user_pseudo_id,
        device_category,
        country,
        coalesce(traffic_source, '(direct)') as traffic_source,
        coalesce(traffic_medium, '(none)') as traffic_medium,
        coalesce(campaign_name, '(not set)') as campaign_name,
        purchase_revenue_usd
    from {{ ref('stg_ga4__events') }}
    where event_name = 'purchase'
      and order_id is not null
)

select
    order_id,
    min(event_date) as order_date,
    any_value(user_pseudo_id) as user_pseudo_id,
    any_value(device_category) as device_category,
    any_value(country) as country,
    any_value(traffic_source) as traffic_source,
    any_value(traffic_medium) as traffic_medium,
    any_value(campaign_name) as campaign_name,
    sum(coalesce(purchase_revenue_usd, 0)) as gross_revenue_usd
from purchase_events
group by 1

