"""Dashboard service used by the backend API and the Streamlit UI."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from cfo_panel.services.bigquery_repository import (
    BigQueryDashboardRepository,
    QueryResult,
    WarehouseUnavailableError,
)
from cfo_panel.settings import WarehouseSettings


SAMPLE_ORDERS: list[dict[str, Any]] = [
    {
        "order_id": "ORD-1001",
        "order_date": "2021-01-24",
        "traffic_source": "google",
        "traffic_medium": "cpc",
        "campaign_name": "brand-search",
        "country": "United States",
        "device_category": "desktop",
        "gross_revenue_usd": 320.0,
        "refund_amount_usd": 0.0,
        "cogs_usd": 172.0,
    },
    {
        "order_id": "ORD-1002",
        "order_date": "2021-01-24",
        "traffic_source": "direct",
        "traffic_medium": "(none)",
        "campaign_name": "returning-customers",
        "country": "United States",
        "device_category": "mobile",
        "gross_revenue_usd": 180.0,
        "refund_amount_usd": 0.0,
        "cogs_usd": 102.0,
    },
    {
        "order_id": "ORD-1003",
        "order_date": "2021-01-25",
        "traffic_source": "instagram",
        "traffic_medium": "paid_social",
        "campaign_name": "winter-sale",
        "country": "Canada",
        "device_category": "mobile",
        "gross_revenue_usd": 240.0,
        "refund_amount_usd": 30.0,
        "cogs_usd": 128.0,
    },
    {
        "order_id": "ORD-1004",
        "order_date": "2021-01-25",
        "traffic_source": "email",
        "traffic_medium": "newsletter",
        "campaign_name": "vip-drop",
        "country": "United States",
        "device_category": "desktop",
        "gross_revenue_usd": 150.0,
        "refund_amount_usd": 0.0,
        "cogs_usd": 78.0,
    },
    {
        "order_id": "ORD-1005",
        "order_date": "2021-01-26",
        "traffic_source": "google",
        "traffic_medium": "cpc",
        "campaign_name": "generic-search",
        "country": "United Kingdom",
        "device_category": "desktop",
        "gross_revenue_usd": 410.0,
        "refund_amount_usd": 0.0,
        "cogs_usd": 230.0,
    },
    {
        "order_id": "ORD-1006",
        "order_date": "2021-01-26",
        "traffic_source": "direct",
        "traffic_medium": "(none)",
        "campaign_name": "returning-customers",
        "country": "Germany",
        "device_category": "mobile",
        "gross_revenue_usd": 90.0,
        "refund_amount_usd": 0.0,
        "cogs_usd": 51.0,
    },
    {
        "order_id": "ORD-1007",
        "order_date": "2021-01-27",
        "traffic_source": "affiliate",
        "traffic_medium": "referral",
        "campaign_name": "partner-launch",
        "country": "United States",
        "device_category": "tablet",
        "gross_revenue_usd": 275.0,
        "refund_amount_usd": 50.0,
        "cogs_usd": 149.0,
    },
    {
        "order_id": "ORD-1008",
        "order_date": "2021-01-27",
        "traffic_source": "google",
        "traffic_medium": "cpc",
        "campaign_name": "brand-search",
        "country": "United States",
        "device_category": "desktop",
        "gross_revenue_usd": 190.0,
        "refund_amount_usd": 0.0,
        "cogs_usd": 104.0,
    },
    {
        "order_id": "ORD-1009",
        "order_date": "2021-01-28",
        "traffic_source": "instagram",
        "traffic_medium": "paid_social",
        "campaign_name": "creator-collab",
        "country": "France",
        "device_category": "mobile",
        "gross_revenue_usd": 355.0,
        "refund_amount_usd": 0.0,
        "cogs_usd": 189.0,
    },
    {
        "order_id": "ORD-1010",
        "order_date": "2021-01-28",
        "traffic_source": "email",
        "traffic_medium": "newsletter",
        "campaign_name": "payday-push",
        "country": "United States",
        "device_category": "desktop",
        "gross_revenue_usd": 165.0,
        "refund_amount_usd": 0.0,
        "cogs_usd": 88.0,
    },
    {
        "order_id": "ORD-1011",
        "order_date": "2021-01-29",
        "traffic_source": "direct",
        "traffic_medium": "(none)",
        "campaign_name": "returning-customers",
        "country": "United States",
        "device_category": "mobile",
        "gross_revenue_usd": 130.0,
        "refund_amount_usd": 0.0,
        "cogs_usd": 74.0,
    },
    {
        "order_id": "ORD-1012",
        "order_date": "2021-01-29",
        "traffic_source": "google",
        "traffic_medium": "cpc",
        "campaign_name": "generic-search",
        "country": "Canada",
        "device_category": "desktop",
        "gross_revenue_usd": 460.0,
        "refund_amount_usd": 20.0,
        "cogs_usd": 260.0,
    },
    {
        "order_id": "ORD-1013",
        "order_date": "2021-01-30",
        "traffic_source": "affiliate",
        "traffic_medium": "referral",
        "campaign_name": "partner-launch",
        "country": "United Kingdom",
        "device_category": "desktop",
        "gross_revenue_usd": 210.0,
        "refund_amount_usd": 0.0,
        "cogs_usd": 121.0,
    },
    {
        "order_id": "ORD-1014",
        "order_date": "2021-01-30",
        "traffic_source": "instagram",
        "traffic_medium": "paid_social",
        "campaign_name": "winter-sale",
        "country": "Germany",
        "device_category": "mobile",
        "gross_revenue_usd": 300.0,
        "refund_amount_usd": 60.0,
        "cogs_usd": 158.0,
    },
    {
        "order_id": "ORD-1015",
        "order_date": "2021-01-31",
        "traffic_source": "email",
        "traffic_medium": "newsletter",
        "campaign_name": "vip-drop",
        "country": "United States",
        "device_category": "desktop",
        "gross_revenue_usd": 175.0,
        "refund_amount_usd": 0.0,
        "cogs_usd": 94.0,
    },
]


def _round(value: float) -> float:
    return round(value, 2)


def _compute_financials(orders: list[dict[str, Any]]) -> dict[str, float]:
    gross_revenue_usd = sum(float(order["gross_revenue_usd"]) for order in orders)
    refund_amount_usd = sum(float(order["refund_amount_usd"]) for order in orders)
    net_revenue_usd = gross_revenue_usd - refund_amount_usd
    gross_margin_usd = net_revenue_usd - sum(float(order["cogs_usd"]) for order in orders)
    order_count = len(orders)
    refund_rate = refund_amount_usd / gross_revenue_usd if gross_revenue_usd else 0.0
    aov_usd = net_revenue_usd / order_count if order_count else 0.0

    return {
        "gross_revenue_usd": _round(gross_revenue_usd),
        "refund_amount_usd": _round(refund_amount_usd),
        "net_revenue_usd": _round(net_revenue_usd),
        "gross_margin_usd": _round(gross_margin_usd),
        "refund_rate": _round(refund_rate),
        "aov_usd": _round(aov_usd),
    }


def list_orders(channel: str | None = None) -> list[dict[str, Any]]:
    selected_channel = channel.lower() if channel else None
    filtered_orders = [
        order
        for order in SAMPLE_ORDERS
        if not selected_channel or str(order["traffic_source"]).lower() == selected_channel
    ]
    return sorted(
        filtered_orders,
        key=lambda item: (str(item["order_date"]), str(item["order_id"])),
        reverse=True,
    )


def build_daily_kpis(orders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped_orders: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for order in orders:
        grouped_orders[str(order["order_date"])].append(order)

    daily_kpis: list[dict[str, Any]] = []
    for order_date in sorted(grouped_orders):
        day_orders = grouped_orders[order_date]
        financials = _compute_financials(day_orders)
        daily_kpis.append(
            {
                "order_date": order_date,
                "order_count": len(day_orders),
                **financials,
            }
        )

    return daily_kpis


def build_channel_performance(orders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped_orders: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for order in orders:
        key = (
            str(order["traffic_source"]),
            str(order["traffic_medium"]),
            str(order["campaign_name"]),
        )
        grouped_orders[key].append(order)

    total_net_revenue = sum(
        float(order["gross_revenue_usd"]) - float(order["refund_amount_usd"]) for order in orders
    )

    channel_rows: list[dict[str, Any]] = []
    for channel_key, channel_orders in grouped_orders.items():
        traffic_source, traffic_medium, campaign_name = channel_key
        financials = _compute_financials(channel_orders)
        revenue_share = (
            financials["net_revenue_usd"] / total_net_revenue if total_net_revenue else 0.0
        )
        channel_rows.append(
            {
                "traffic_source": traffic_source,
                "traffic_medium": traffic_medium,
                "campaign_name": campaign_name,
                "order_count": len(channel_orders),
                "revenue_share": _round(revenue_share),
                **financials,
            }
        )

    return sorted(
        channel_rows,
        key=lambda row: (float(row["net_revenue_usd"]), int(row["order_count"])),
        reverse=True,
    )


def build_recent_orders(orders: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    recent_orders: list[dict[str, Any]] = []
    for order in orders[:limit]:
        net_revenue_usd = float(order["gross_revenue_usd"]) - float(order["refund_amount_usd"])
        gross_margin_usd = net_revenue_usd - float(order["cogs_usd"])
        recent_orders.append(
            {
                **order,
                "net_revenue_usd": _round(net_revenue_usd),
                "gross_margin_usd": _round(gross_margin_usd),
            }
        )

    return recent_orders


def _build_sample_source_events(
    orders: list[dict[str, Any]], limit: int = 8
) -> list[dict[str, Any]]:
    raw_events: list[dict[str, Any]] = []
    for order in orders:
        raw_events.append(
            {
                "raw_event_date": str(order["order_date"]).replace("-", ""),
                "raw_event_name": "purchase",
                "raw_transaction_id": order["order_id"],
                "raw_purchase_revenue_in_usd": float(order["gross_revenue_usd"]),
                "raw_refund_value_in_usd": 0.0,
                "raw_device_category": order["device_category"],
                "raw_country": order["country"],
                "raw_source": order["traffic_source"],
                "raw_medium": order["traffic_medium"],
                "raw_campaign": order["campaign_name"],
            }
        )
        if float(order["refund_amount_usd"]) > 0:
            raw_events.append(
                {
                    "raw_event_date": str(order["order_date"]).replace("-", ""),
                    "raw_event_name": "refund",
                    "raw_transaction_id": order["order_id"],
                    "raw_purchase_revenue_in_usd": 0.0,
                    "raw_refund_value_in_usd": float(order["refund_amount_usd"]),
                    "raw_device_category": order["device_category"],
                    "raw_country": order["country"],
                    "raw_source": order["traffic_source"],
                    "raw_medium": order["traffic_medium"],
                    "raw_campaign": order["campaign_name"],
                }
            )

    raw_events.sort(
        key=lambda row: (
            str(row["raw_event_date"]),
            str(row["raw_transaction_id"]),
            str(row["raw_event_name"]),
        ),
        reverse=True,
    )
    return raw_events[:limit]


def _build_staging_preview_from_orders(
    orders: list[dict[str, Any]], limit: int = 8
) -> list[dict[str, Any]]:
    staging_rows: list[dict[str, Any]] = []
    for raw_event in _build_sample_source_events(orders, limit=limit * 2):
        staging_rows.append(
            {
                "event_date": (
                    f"{raw_event['raw_event_date'][0:4]}-"
                    f"{raw_event['raw_event_date'][4:6]}-"
                    f"{raw_event['raw_event_date'][6:8]}"
                ),
                "event_name": raw_event["raw_event_name"],
                "user_pseudo_id": "sample-user",
                "order_id": raw_event["raw_transaction_id"],
                "purchase_revenue_usd": raw_event["raw_purchase_revenue_in_usd"],
                "refund_value_usd": raw_event["raw_refund_value_in_usd"],
                "device_category": raw_event["raw_device_category"],
                "country": raw_event["raw_country"],
                "traffic_source": raw_event["raw_source"],
                "traffic_medium": raw_event["raw_medium"],
                "campaign_name": raw_event["raw_campaign"],
            }
        )
    return staging_rows[:limit]


def _build_order_preview(orders: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    return build_recent_orders(orders, limit=limit)


def _build_mart_preview(orders: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    return build_daily_kpis(orders)[:limit]


def _build_data_journey(
    orders: list[dict[str, Any]],
    *,
    channel: str | None,
    source_label: str,
    source_detail: str,
    repository: BigQueryDashboardRepository | None,
    is_live: bool,
) -> dict[str, Any]:
    source_preview = _build_sample_source_events(orders)
    staging_preview = _build_staging_preview_from_orders(orders)

    if repository is not None and is_live:
        if hasattr(repository, "fetch_source_event_preview"):
            try:
                source_preview = repository.fetch_source_event_preview(channel=channel)
            except WarehouseUnavailableError:
                pass
        if hasattr(repository, "fetch_staging_preview"):
            try:
                staging_preview = repository.fetch_staging_preview(channel=channel)
            except WarehouseUnavailableError:
                pass

    order_preview = _build_order_preview(orders)
    mart_preview = _build_mart_preview(orders)

    return {
        "headline": "We turn raw ecommerce events into CFO-ready decision support data.",
        "summary": (
            "This product cleans incoming purchase and refund events, aggregates them at the "
            "order level, and transforms them into executive KPI tables."
        ),
        "steps": [
            {
                "stage": "source",
                "title": "1. Raw Source Events",
                "grain": "event",
                "description": (
                    f"Incoming data is read from {source_label}. At this stage the payload still "
                    "contains event names, nested fields, and raw source column names."
                ),
                "row_count": len(source_preview),
            },
            {
                "stage": "staging",
                "title": "2. Staging Layer",
                "grain": "clean event",
                "description": (
                    "Raw events are cleaned, date types are standardized, and the fields needed "
                    "for analytics are renamed into business-friendly columns."
                ),
                "row_count": len(staging_preview),
            },
            {
                "stage": "order_details",
                "title": "3. Order-Level Model",
                "grain": "order",
                "description": (
                    "Purchase and refund events are combined at the order level. Net revenue, "
                    "refund amount, and gross margin proxy fields are calculated here."
                ),
                "row_count": len(order_preview),
            },
            {
                "stage": "mart",
                "title": "4. CFO Mart",
                "grain": "daily KPI",
                "description": (
                    "The final layer exposes the KPI tables a CFO actually uses: net revenue, "
                    "AOV, refund rate, and channel performance."
                ),
                "row_count": len(mart_preview),
            },
        ],
        "source_name": source_label,
        "source_detail": source_detail,
        "source_preview": source_preview,
        "staging_preview": staging_preview,
        "order_preview": order_preview,
        "mart_preview": mart_preview,
    }


def build_overview(orders: list[dict[str, Any]]) -> dict[str, Any]:
    financials = _compute_financials(orders)
    daily_kpis = build_daily_kpis(orders)
    channel_performance = build_channel_performance(orders)

    best_day = max(
        daily_kpis,
        key=lambda row: float(row["net_revenue_usd"]),
        default={"order_date": None, "net_revenue_usd": 0.0},
    )
    top_channel = channel_performance[0] if channel_performance else None

    return {
        "total_orders": len(orders),
        "active_channels": len({str(order["traffic_source"]) for order in orders}),
        "best_day": best_day["order_date"],
        "best_day_net_revenue_usd": best_day["net_revenue_usd"],
        "top_channel": top_channel["traffic_source"] if top_channel else None,
        "top_channel_net_revenue_usd": top_channel["net_revenue_usd"] if top_channel else 0.0,
        **financials,
    }


def _build_payload_from_orders(
    orders: list[dict[str, Any]],
    *,
    channel: str | None,
    source_mode: str,
    source_label: str,
    source_detail: str,
    is_live: bool,
    repository: BigQueryDashboardRepository | None,
) -> dict[str, Any]:
    all_orders = list_orders() if source_mode == "sample" else orders
    order_dates = [str(order["order_date"]) for order in orders]

    return {
        "overview": build_overview(orders),
        "daily_kpis": build_daily_kpis(orders),
        "channel_performance": build_channel_performance(orders),
        "recent_orders": build_recent_orders(orders),
        "available_channels": sorted({str(order["traffic_source"]) for order in all_orders}),
        "filters": {"channel": channel},
        "data_source": {
            "mode": source_mode,
            "label": source_label,
            "detail": source_detail,
            "is_live": is_live,
        },
        "data_journey": _build_data_journey(
            orders,
            channel=channel,
            source_label=source_label,
            source_detail=source_detail,
            repository=repository,
            is_live=is_live,
        ),
        "data_period": {
            "start_date": min(order_dates) if order_dates else None,
            "end_date": max(order_dates) if order_dates else None,
        },
    }


def build_dashboard_payload(
    channel: str | None = None,
    repository: BigQueryDashboardRepository | None = None,
    settings: WarehouseSettings | None = None,
) -> dict[str, Any]:
    resolved_settings = settings or WarehouseSettings.from_env()

    if repository is None and resolved_settings.can_query_bigquery:
        repository = BigQueryDashboardRepository(settings=resolved_settings)

    if repository is not None:
        try:
            warehouse_result: QueryResult = repository.fetch_order_rows(channel=channel)
            return _build_payload_from_orders(
                warehouse_result.orders,
                channel=channel,
                source_mode=warehouse_result.source_mode,
                source_label=warehouse_result.source_label,
                source_detail=warehouse_result.source_detail,
                is_live=True,
                repository=repository,
            )
        except WarehouseUnavailableError:
            pass

    orders = list_orders(channel=channel)
    return _build_payload_from_orders(
        orders,
        channel=channel,
        source_mode="sample",
        source_label="Embedded sample data",
        source_detail="In-app demo order dataset",
        is_live=False,
        repository=None,
    )
