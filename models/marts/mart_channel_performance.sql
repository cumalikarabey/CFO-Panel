select
    order_date,
    traffic_source,
    traffic_medium,
    campaign_name,
    count(*) as order_count,
    sum(gross_revenue_usd) as gross_revenue_usd,
    sum(refund_amount_usd) as refund_amount_usd,
    sum(net_revenue_usd) as net_revenue_usd,
    sum(gross_margin_usd) as gross_margin_usd,
    safe_divide(sum(refund_amount_usd), nullif(sum(gross_revenue_usd), 0)) as refund_rate,
    avg(net_revenue_usd) as avg_order_value_usd
from {{ ref('mart_order_details') }}
group by 1, 2, 3, 4
