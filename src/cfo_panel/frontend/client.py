"""Client utilities for fetching dashboard data."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

from cfo_panel.services.dashboard_service import build_dashboard_payload


@dataclass
class DashboardFetchResult:
    payload: dict
    source_label: str
    api_available: bool


class DashboardClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def fetch_dashboard(self, channel: str | None = None) -> DashboardFetchResult:
        channel_query = f"?channel={quote(channel)}" if channel else ""
        endpoint = f"{self.base_url}/api/v1/dashboard{channel_query}"

        try:
            with urlopen(endpoint, timeout=2) as response:
                payload = json.load(response)
            return DashboardFetchResult(
                payload=payload,
                source_label=payload.get("data_source", {}).get("label", "Canli API"),
                api_available=True,
            )
        except (HTTPError, URLError, TimeoutError, ValueError):
            payload = build_dashboard_payload(channel=channel)
            return DashboardFetchResult(
                payload=payload,
                source_label=payload.get("data_source", {}).get("label", "Embedded sample data"),
                api_available=False,
            )
