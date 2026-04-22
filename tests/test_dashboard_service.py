from __future__ import annotations

import unittest

from cfo_panel.services.bigquery_repository import QueryResult, WarehouseUnavailableError
from cfo_panel.services.dashboard_service import (
    build_channel_performance,
    build_dashboard_payload,
    build_overview,
    list_orders,
)


class SuccessfulRepositoryStub:
    def fetch_order_rows(self, channel: str | None = None) -> QueryResult:
        orders = list_orders(channel=channel)
        return QueryResult(
            orders=orders,
            source_mode="bigquery_mart",
            source_label="BigQuery dbt mart",
            source_detail="demo_project.cfo_panel_dev.mart_order_details",
        )

    def fetch_source_event_preview(self, channel: str | None = None, limit: int = 8) -> list[dict]:
        return [
            {
                "raw_event_date": "20210131",
                "raw_event_name": "purchase",
                "raw_transaction_id": "ORD-1015",
            }
        ]

    def fetch_staging_preview(self, channel: str | None = None, limit: int = 8) -> list[dict]:
        return [
            {
                "event_date": "2021-01-31",
                "event_name": "purchase",
                "order_id": "ORD-1015",
            }
        ]


class FailingRepositoryStub:
    def fetch_order_rows(self, channel: str | None = None) -> QueryResult:
        raise WarehouseUnavailableError("credentials missing")


class DashboardServiceTests(unittest.TestCase):
    def test_overview_contains_core_metrics(self) -> None:
        overview = build_overview(list_orders())

        self.assertEqual(overview["total_orders"], 15)
        self.assertEqual(overview["active_channels"], 5)
        self.assertGreater(overview["net_revenue_usd"], 0)
        self.assertGreater(overview["gross_margin_usd"], 0)

    def test_channel_filter_limits_orders_to_selected_source(self) -> None:
        google_orders = list_orders(channel="google")

        self.assertTrue(google_orders)
        self.assertTrue(all(order["traffic_source"] == "google" for order in google_orders))

    def test_channel_performance_is_sorted_by_net_revenue(self) -> None:
        channel_rows = build_channel_performance(list_orders())

        self.assertGreaterEqual(
            channel_rows[0]["net_revenue_usd"],
            channel_rows[-1]["net_revenue_usd"],
        )

    def test_dashboard_payload_exposes_sections_needed_by_ui(self) -> None:
        payload = build_dashboard_payload()

        self.assertIn("overview", payload)
        self.assertIn("daily_kpis", payload)
        self.assertIn("channel_performance", payload)
        self.assertIn("recent_orders", payload)
        self.assertIn("data_source", payload)
        self.assertIn("data_journey", payload)
        self.assertEqual(payload["data_period"]["start_date"], "2021-01-24")
        self.assertEqual(payload["data_period"]["end_date"], "2021-01-31")

    def test_dashboard_payload_uses_bigquery_result_when_repository_is_available(self) -> None:
        payload = build_dashboard_payload(repository=SuccessfulRepositoryStub())

        self.assertEqual(payload["data_source"]["mode"], "bigquery_mart")
        self.assertTrue(payload["data_source"]["is_live"])
        self.assertEqual(payload["data_journey"]["source_preview"][0]["raw_event_name"], "purchase")
        self.assertEqual(payload["data_journey"]["staging_preview"][0]["event_name"], "purchase")

    def test_dashboard_payload_falls_back_to_sample_data_on_repository_failure(self) -> None:
        payload = build_dashboard_payload(repository=FailingRepositoryStub())

        self.assertEqual(payload["data_source"]["mode"], "sample")
        self.assertFalse(payload["data_source"]["is_live"])
        self.assertTrue(payload["data_journey"]["source_preview"])


if __name__ == "__main__":
    unittest.main()
