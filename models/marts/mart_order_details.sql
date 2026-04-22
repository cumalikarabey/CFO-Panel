with orders as (
    select *
    from {{ ref('int_orders') }}
),
refunds as (
    select *
    from {{ ref('int_refunds') }}
)

select
    orders.order_id,
    orders.order_date,
    orders.user_pseudo_id,
    orders.device_category,
    orders.country,
    orders.traffic_source,
    orders.traffic_medium,
    orders.campaign_name,
    orders.gross_revenue_usd,
    coalesce(refunds.refund_amount_usd, 0) as refund_amount_usd,
    orders.gross_revenue_usd - coalesce(refunds.refund_amount_usd, 0) as net_revenue_usd,
    orders.gross_revenue_usd * {{ var('assumed_cogs_ratio') }} as cogs_usd,
    (orders.gross_revenue_usd - coalesce(refunds.refund_amount_usd, 0))
        - (orders.gross_revenue_usd * {{ var('assumed_cogs_ratio') }}) as gross_margin_usd,
    safe_divide(
        coalesce(refunds.refund_amount_usd, 0),
        nullif(orders.gross_revenue_usd, 0)
    ) as refund_rate
from orders
left join refunds
    on orders.order_id = refunds.order_id
