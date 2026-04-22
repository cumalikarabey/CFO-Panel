"""Response schemas for the CFO Panel API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class OverviewResponse(BaseModel):
    total_orders: int
    active_channels: int
    best_day: str | None
    best_day_net_revenue_usd: float
    top_channel: str | None
    top_channel_net_revenue_usd: float
    gross_revenue_usd: float
    refund_amount_usd: float
    net_revenue_usd: float
    gross_margin_usd: float
    refund_rate: float
    aov_usd: float


class DailyKpiResponse(BaseModel):
    order_date: str
    order_count: int
    gross_revenue_usd: float
    refund_amount_usd: float
    net_revenue_usd: float
    gross_margin_usd: float
    refund_rate: float
    aov_usd: float


class ChannelPerformanceResponse(BaseModel):
    traffic_source: str
    traffic_medium: str
    campaign_name: str
    order_count: int
    revenue_share: float
    gross_revenue_usd: float
    refund_amount_usd: float
    net_revenue_usd: float
    gross_margin_usd: float
    refund_rate: float
    aov_usd: float


class RecentOrderResponse(BaseModel):
    order_id: str
    order_date: str
    traffic_source: str
    traffic_medium: str
    campaign_name: str
    country: str
    device_category: str
    gross_revenue_usd: float
    refund_amount_usd: float
    cogs_usd: float
    net_revenue_usd: float
    gross_margin_usd: float


class DataPeriodResponse(BaseModel):
    start_date: str | None
    end_date: str | None


class DashboardFiltersResponse(BaseModel):
    channel: str | None


class DataSourceResponse(BaseModel):
    mode: str
    label: str
    detail: str
    is_live: bool


class DataJourneyStepResponse(BaseModel):
    stage: str
    title: str
    grain: str
    description: str
    row_count: int


class DataJourneyResponse(BaseModel):
    headline: str
    summary: str
    steps: list[DataJourneyStepResponse]
    source_name: str
    source_detail: str
    source_preview: list[dict[str, Any]]
    staging_preview: list[dict[str, Any]]
    order_preview: list[dict[str, Any]]
    mart_preview: list[dict[str, Any]]


class DashboardResponse(BaseModel):
    overview: OverviewResponse
    daily_kpis: list[DailyKpiResponse]
    channel_performance: list[ChannelPerformanceResponse]
    recent_orders: list[RecentOrderResponse]
    available_channels: list[str]
    filters: DashboardFiltersResponse
    data_source: DataSourceResponse
    data_journey: DataJourneyResponse
    data_period: DataPeriodResponse
