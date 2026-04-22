"""Warehouse access for the CFO dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from google.api_core.exceptions import BadRequest, Forbidden, GoogleAPIError, NotFound
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery

from cfo_panel.settings import WarehouseSettings


class WarehouseUnavailableError(RuntimeError):
    """Raised when the dashboard cannot be loaded from BigQuery."""


@dataclass(frozen=True)
class QueryResult:
    orders: list[dict[str, Any]]
    source_mode: str
    source_label: str
    source_detail: str


class BigQueryDashboardRepository:
    """Loads dashboard order-level rows from dbt marts or the raw GA4 source."""

    def __init__(self, settings: WarehouseSettings | None = None) -> None:
        self.settings = settings or WarehouseSettings.from_env()
        self._client: bigquery.Client | None = None

    @property
    def client(self) -> bigquery.Client:
        if self._client is None:
            try:
                client_kwargs: dict[str, Any] = {"location": self.settings.bigquery_location}
                if self.settings.bigquery_project:
                    client_kwargs["project"] = self.settings.bigquery_project
                self._client = bigquery.Client(**client_kwargs)
            except DefaultCredentialsError as exc:
                raise WarehouseUnavailableError(
                    "BigQuery credentials were not found. "
                    "Set GOOGLE_APPLICATION_CREDENTIALS or configure Application Default Credentials."
                ) from exc
        return self._client

    def fetch_order_rows(self, channel: str | None = None) -> QueryResult:
        if not self.settings.can_query_bigquery:
            raise WarehouseUnavailableError("BigQuery access is not configured yet.")

        attempts: list[Any] = []
        if self.settings.has_mart_target and self.settings.prefer_marts:
            attempts.append(self._query_mart_order_rows)
        if self.settings.allow_source_queries:
            attempts.append(self._query_source_order_rows)
        if self.settings.has_mart_target and not self.settings.prefer_marts:
            attempts.append(self._query_mart_order_rows)

        errors: list[str] = []
        for attempt in attempts:
            try:
                return attempt(channel=channel)
            except WarehouseUnavailableError as exc:
                errors.append(str(exc))

        raise WarehouseUnavailableError(" | ".join(errors))

    def _run_query(
        self,
        query: str,
        parameters: list[bigquery.ScalarQueryParameter],
    ) -> list[dict[str, Any]]:
        try:
            job_config = bigquery.QueryJobConfig(query_parameters=parameters)
            rows = self.client.query(query, job_config=job_config).result()
        except (BadRequest, Forbidden, GoogleAPIError, NotFound) as exc:
            raise WarehouseUnavailableError(str(exc)) from exc

        normalized_rows: list[dict[str, Any]] = []
        for row in rows:
            normalized_rows.append(
                {key: self._normalize_value(value) for key, value in dict(row.items()).items()}
            )
        return normalized_rows

    def _query_mart_order_rows(self, channel: str | None = None) -> QueryResult:
        try:
            order_details_table = self.settings.mart_table("mart_order_details")
        except ValueError as exc:
            raise WarehouseUnavailableError(str(exc)) from exc

        query = f"""
        select
            cast(order_id as string) as order_id,
            cast(order_date as string) as order_date,
            cast(user_pseudo_id as string) as user_pseudo_id,
            cast(device_category as string) as device_category,
            cast(country as string) as country,
            cast(traffic_source as string) as traffic_source,
            cast(traffic_medium as string) as traffic_medium,
            cast(campaign_name as string) as campaign_name,
            cast(gross_revenue_usd as float64) as gross_revenue_usd,
            cast(refund_amount_usd as float64) as refund_amount_usd,
            cast(cogs_usd as float64) as cogs_usd
        from {order_details_table}
        where (@channel is null or lower(traffic_source) = lower(@channel))
        order by order_date desc, order_id desc
        """

        rows = self._run_query(
            query,
            parameters=[
                bigquery.ScalarQueryParameter("channel", "STRING", channel),
            ],
        )
        return QueryResult(
            orders=rows,
            source_mode="bigquery_mart",
            source_label="BigQuery dbt mart",
            source_detail=f"{self.settings.mart_project}.{self.settings.mart_dataset}.mart_order_details",
        )

    def _query_source_order_rows(self, channel: str | None = None) -> QueryResult:
        source_table = (
            f"`{self.settings.ga4_project_id}.{self.settings.ga4_dataset}.events_*`"
        )
        query = f"""
        with source_events as (
            select
                parse_date('%Y%m%d', event_date) as event_date,
                event_name,
                user_pseudo_id,
                ecommerce.transaction_id as order_id,
                ecommerce.purchase_revenue_in_usd as purchase_revenue_usd,
                ecommerce.refund_value_in_usd as refund_value_usd,
                device.category as device_category,
                geo.country as country,
                coalesce(traffic_source.source, '(direct)') as traffic_source,
                coalesce(traffic_source.medium, '(none)') as traffic_medium,
                coalesce(traffic_source.name, '(not set)') as campaign_name
            from {source_table}
            where _table_suffix between @start_date and @end_date
        ),
        purchases as (
            select
                order_id,
                min(event_date) as order_date,
                any_value(user_pseudo_id) as user_pseudo_id,
                any_value(device_category) as device_category,
                any_value(country) as country,
                any_value(traffic_source) as traffic_source,
                any_value(traffic_medium) as traffic_medium,
                any_value(campaign_name) as campaign_name,
                sum(coalesce(purchase_revenue_usd, 0.0)) as gross_revenue_usd
            from source_events
            where event_name = 'purchase'
              and order_id is not null
            group by 1
        ),
        refunds as (
            select
                order_id,
                sum(coalesce(refund_value_usd, 0.0)) as refund_amount_usd
            from source_events
            where event_name = 'refund'
              and order_id is not null
            group by 1
        )
        select
            cast(purchases.order_id as string) as order_id,
            cast(purchases.order_date as string) as order_date,
            cast(purchases.user_pseudo_id as string) as user_pseudo_id,
            cast(purchases.device_category as string) as device_category,
            cast(purchases.country as string) as country,
            cast(purchases.traffic_source as string) as traffic_source,
            cast(purchases.traffic_medium as string) as traffic_medium,
            cast(purchases.campaign_name as string) as campaign_name,
            cast(purchases.gross_revenue_usd as float64) as gross_revenue_usd,
            cast(coalesce(refunds.refund_amount_usd, 0.0) as float64) as refund_amount_usd,
            cast(purchases.gross_revenue_usd * @assumed_cogs_ratio as float64) as cogs_usd
        from purchases
        left join refunds
            on purchases.order_id = refunds.order_id
        where (@channel is null or lower(purchases.traffic_source) = lower(@channel))
        order by purchases.order_date desc, purchases.order_id desc
        """

        rows = self._run_query(
            query,
            parameters=[
                bigquery.ScalarQueryParameter("start_date", "STRING", self.settings.start_date),
                bigquery.ScalarQueryParameter("end_date", "STRING", self.settings.end_date),
                bigquery.ScalarQueryParameter(
                    "assumed_cogs_ratio", "FLOAT64", self.settings.assumed_cogs_ratio
                ),
                bigquery.ScalarQueryParameter("channel", "STRING", channel),
            ],
        )
        return QueryResult(
            orders=rows,
            source_mode="ga4_source_query",
            source_label="BigQuery GA4 source query",
            source_detail=(
                f"{self.settings.ga4_project_id}.{self.settings.ga4_dataset}.events_*"
            ),
        )

    def fetch_source_event_preview(
        self, channel: str | None = None, limit: int = 8
    ) -> list[dict[str, Any]]:
        source_table = (
            f"`{self.settings.ga4_project_id}.{self.settings.ga4_dataset}.events_*`"
        )
        query = f"""
        select
            cast(event_date as string) as raw_event_date,
            cast(event_name as string) as raw_event_name,
            cast(ecommerce.transaction_id as string) as raw_transaction_id,
            cast(ecommerce.purchase_revenue_in_usd as float64) as raw_purchase_revenue_in_usd,
            cast(ecommerce.refund_value_in_usd as float64) as raw_refund_value_in_usd,
            cast(device.category as string) as raw_device_category,
            cast(geo.country as string) as raw_country,
            cast(coalesce(traffic_source.source, '(direct)') as string) as raw_source,
            cast(coalesce(traffic_source.medium, '(none)') as string) as raw_medium,
            cast(coalesce(traffic_source.name, '(not set)') as string) as raw_campaign
        from {source_table}
        where _table_suffix between @start_date and @end_date
          and event_name in ('purchase', 'refund')
          and ecommerce.transaction_id is not null
          and (@channel is null or lower(coalesce(traffic_source.source, '(direct)')) = lower(@channel))
        order by event_date desc, ecommerce.transaction_id desc
        limit @limit
        """

        return self._run_query(
            query,
            parameters=[
                bigquery.ScalarQueryParameter("start_date", "STRING", self.settings.start_date),
                bigquery.ScalarQueryParameter("end_date", "STRING", self.settings.end_date),
                bigquery.ScalarQueryParameter("channel", "STRING", channel),
                bigquery.ScalarQueryParameter("limit", "INT64", limit),
            ],
        )

    def fetch_staging_preview(
        self, channel: str | None = None, limit: int = 8
    ) -> list[dict[str, Any]]:
        source_table = (
            f"`{self.settings.ga4_project_id}.{self.settings.ga4_dataset}.events_*`"
        )
        query = f"""
        select
            cast(parse_date('%Y%m%d', event_date) as string) as event_date,
            cast(event_name as string) as event_name,
            cast(user_pseudo_id as string) as user_pseudo_id,
            cast(ecommerce.transaction_id as string) as order_id,
            cast(ecommerce.purchase_revenue_in_usd as float64) as purchase_revenue_usd,
            cast(ecommerce.refund_value_in_usd as float64) as refund_value_usd,
            cast(device.category as string) as device_category,
            cast(geo.country as string) as country,
            cast(coalesce(traffic_source.source, '(direct)') as string) as traffic_source,
            cast(coalesce(traffic_source.medium, '(none)') as string) as traffic_medium,
            cast(coalesce(traffic_source.name, '(not set)') as string) as campaign_name
        from {source_table}
        where _table_suffix between @start_date and @end_date
          and event_name in ('purchase', 'refund')
          and ecommerce.transaction_id is not null
          and (@channel is null or lower(coalesce(traffic_source.source, '(direct)')) = lower(@channel))
        order by event_date desc, ecommerce.transaction_id desc
        limit @limit
        """

        return self._run_query(
            query,
            parameters=[
                bigquery.ScalarQueryParameter("start_date", "STRING", self.settings.start_date),
                bigquery.ScalarQueryParameter("end_date", "STRING", self.settings.end_date),
                bigquery.ScalarQueryParameter("channel", "STRING", channel),
                bigquery.ScalarQueryParameter("limit", "INT64", limit),
            ],
        )

    def _normalize_value(self, value: Any) -> Any:
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return value
