with refund_events as (
    select
        order_id,
        sum(coalesce(refund_value_usd, 0)) as refund_amount_usd
    from {{ ref('stg_ga4__events') }}
    where event_name = 'refund'
      and order_id is not null
    group by 1
)

select *
from refund_events

