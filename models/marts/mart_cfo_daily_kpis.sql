with order_details as (
    select *
    from {{ ref('mart_order_details') }}
),
daily as (
    select
        order_date,
        count(*) as order_count,
        sum(gross_revenue_usd) as gross_revenue_usd,
        sum(refund_amount_usd) as refund_amount_usd,
        sum(net_revenue_usd) as net_revenue_usd,
        sum(gross_margin_usd) as gross_margin_usd
    from order_details
    group by 1
)

select
    order_date,
    order_count,
    gross_revenue_usd,
    refund_amount_usd,
    net_revenue_usd,
    safe_divide(net_revenue_usd, nullif(order_count, 0)) as aov_usd,
    gross_margin_usd,
    safe_divide(refund_amount_usd, nullif(gross_revenue_usd, 0)) as refund_rate
from daily
