"""FastAPI app exposing the first CFO Panel backend endpoints."""

from __future__ import annotations

from fastapi import FastAPI, Query

from cfo_panel.api.schemas import (
    ChannelPerformanceResponse,
    DataJourneyResponse,
    DashboardResponse,
    OverviewResponse,
    RecentOrderResponse,
)
from cfo_panel.services.dashboard_service import (
    build_channel_performance,
    build_dashboard_payload,
    build_overview,
    build_recent_orders,
    list_orders,
)


app = FastAPI(
    title="CFO Panel API",
    version="0.1.0",
    summary="Backend API for the first CFO analytics dashboard prototype",
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "CFO Panel API is running. Dashboard data is available at /api/v1/dashboard."
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/dashboard", response_model=DashboardResponse)
def dashboard(channel: str | None = Query(default=None)) -> DashboardResponse:
    return DashboardResponse.model_validate(build_dashboard_payload(channel=channel))


@app.get("/api/v1/data-journey", response_model=DataJourneyResponse)
def data_journey(channel: str | None = Query(default=None)) -> DataJourneyResponse:
    payload = build_dashboard_payload(channel=channel)
    return DataJourneyResponse.model_validate(payload["data_journey"])


@app.get("/api/v1/overview", response_model=OverviewResponse)
def overview(channel: str | None = Query(default=None)) -> OverviewResponse:
    return OverviewResponse.model_validate(build_overview(list_orders(channel=channel)))


@app.get("/api/v1/channel-performance", response_model=list[ChannelPerformanceResponse])
def channel_performance(
    channel: str | None = Query(default=None),
) -> list[ChannelPerformanceResponse]:
    return [
        ChannelPerformanceResponse.model_validate(row)
        for row in build_channel_performance(list_orders(channel=channel))
    ]


@app.get("/api/v1/recent-orders", response_model=list[RecentOrderResponse])
def recent_orders(channel: str | None = Query(default=None)) -> list[RecentOrderResponse]:
    return [
        RecentOrderResponse.model_validate(row)
        for row in build_recent_orders(list_orders(channel=channel))
    ]
