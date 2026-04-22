"""Streamlit UI for the first CFO dashboard prototype."""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from cfo_panel.frontend.client import DashboardClient
from cfo_panel.settings import (
    ENV_FILE_PATH,
    WarehouseSettings,
    get_editable_env_values,
    save_editable_env_values,
)


DEFAULT_API_BASE_URL = os.getenv("CFO_PANEL_API_BASE_URL", "http://127.0.0.1:8000")


def format_currency(value: float) -> str:
    return f"${value:,.0f}"


def format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            :root {
                --cream: #f6f1e8;
                --ink: #14213d;
                --slate: #405574;
                --card: rgba(255, 255, 255, 0.78);
                --border: rgba(20, 33, 61, 0.12);
                --teal: #2a9d8f;
                --amber: #f4a261;
                --coral: #e76f51;
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(244, 162, 97, 0.20), transparent 30%),
                    linear-gradient(180deg, #fcfaf5 0%, #f4efe3 100%);
                color: var(--ink);
            }

            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                max-width: 1250px;
            }

            .hero {
                background: linear-gradient(135deg, #14213d 0%, #1f3b5d 58%, #2a9d8f 100%);
                border-radius: 24px;
                padding: 2rem;
                margin-bottom: 1.5rem;
                color: #ffffff;
                box-shadow: 0 20px 60px rgba(20, 33, 61, 0.18);
            }

            .hero-eyebrow {
                font-size: 0.82rem;
                letter-spacing: 0.18em;
                text-transform: uppercase;
                opacity: 0.75;
                margin-bottom: 0.4rem;
            }

            .hero-title {
                font-size: 2.2rem;
                line-height: 1.05;
                margin: 0;
                max-width: 800px;
            }

            .hero-copy {
                margin-top: 0.9rem;
                max-width: 780px;
                color: rgba(255, 255, 255, 0.82);
                font-size: 1rem;
            }

            .source-chip {
                display: inline-block;
                margin-top: 1rem;
                padding: 0.35rem 0.75rem;
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.18);
                font-size: 0.85rem;
            }

            .metric-card {
                background: var(--card);
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 1.15rem 1rem 1rem 1rem;
                min-height: 142px;
                box-shadow: 0 12px 30px rgba(20, 33, 61, 0.06);
                backdrop-filter: blur(12px);
            }

            .metric-title {
                color: var(--slate);
                font-size: 0.86rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                margin-bottom: 0.7rem;
            }

            .metric-value {
                color: var(--ink);
                font-size: 2rem;
                line-height: 1;
                font-weight: 700;
                margin-bottom: 0.55rem;
            }

            .metric-note {
                color: #5f6f86;
                font-size: 0.92rem;
            }

            [data-testid="stMetric"] {
                background: rgba(255, 255, 255, 0.72);
                border: 1px solid rgba(20, 33, 61, 0.10);
                border-radius: 18px;
                padding: 1rem 1rem 0.85rem 1rem;
                box-shadow: 0 10px 24px rgba(20, 33, 61, 0.05);
            }

            [data-testid="stMetricLabel"] {
                color: #5f6f86 !important;
                font-weight: 600;
            }

            [data-testid="stMetricLabel"] * {
                color: #5f6f86 !important;
            }

            [data-testid="stMetricValue"] {
                color: #14213d !important;
            }

            [data-testid="stMetricValue"] * {
                color: #14213d !important;
            }

            [data-testid="stMetricDelta"] {
                color: #2a9d8f !important;
            }

            [data-testid="stMetricDelta"] * {
                color: #2a9d8f !important;
            }

            .journey-card {
                background: rgba(255, 255, 255, 0.72);
                border: 1px solid rgba(20, 33, 61, 0.10);
                border-radius: 18px;
                padding: 1rem;
                min-height: 180px;
                box-shadow: 0 10px 24px rgba(20, 33, 61, 0.05);
            }

            .journey-stage {
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.12em;
                color: #52708d;
                margin-bottom: 0.45rem;
            }

            .journey-title {
                font-size: 1.15rem;
                font-weight: 700;
                color: var(--ink);
                margin-bottom: 0.55rem;
            }

            .journey-grain {
                color: #2a9d8f;
                font-size: 0.86rem;
                margin-bottom: 0.55rem;
            }

            .journey-body {
                color: #53657f;
                font-size: 0.93rem;
                line-height: 1.45;
            }

            .stTabs [data-baseweb="tab-list"] {
                gap: 0.5rem;
            }

            .stTabs [data-baseweb="tab"] {
                background: rgba(255, 255, 255, 0.58);
                border-radius: 999px 999px 0 0;
                padding-left: 0.35rem;
                padding-right: 0.35rem;
            }

            .stTabs [data-baseweb="tab"] p {
                color: #405574 !important;
                font-weight: 600;
            }

            .stTabs [data-baseweb="tab"][aria-selected="true"] p {
                color: #d94841 !important;
            }

            .section-note {
                color: #54657d;
                margin-top: -0.4rem;
                margin-bottom: 1rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(title: str, value: str, note: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_journey_card(stage: str, title: str, grain: str, description: str, row_count: int) -> None:
    st.markdown(
        f"""
        <div class="journey-card">
            <div class="journey-stage">{stage}</div>
            <div class="journey-title">{title}</div>
            <div class="journey-grain">Grain: {grain} | Preview rows: {row_count}</div>
            <div class="journey-body">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header(source_label: str, api_available: bool, is_live: bool) -> None:
    if api_available and is_live:
        connection_text = "The backend connection is active and the dashboard is reading from BigQuery."
    elif api_available and not is_live:
        connection_text = "The backend is running, but the app is currently falling back to sample data."
    else:
        connection_text = "Even without the backend, the UI remains explorable with embedded sample data."
    st.markdown(
        f"""
        <section class="hero">
            <div class="hero-eyebrow">CFO Command Center</div>
            <h1 class="hero-title">Bring revenue, margin, and refund signals into one executive operating view.</h1>
            <p class="hero-copy">
                This first version is a working product slice that shows what the analytics mart becomes in practice.
                You can see the backend KPI layer, the transformation story, and the executive dashboard in one place.
            </p>
            <div class="source-chip">Data source: {source_label} | {connection_text}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_settings_panel() -> None:
    current_settings = WarehouseSettings.from_env()
    env_values = get_editable_env_values()

    with st.sidebar.expander("GCP / BigQuery Settings", expanded=True):
        st.caption(f"These values are saved to `{ENV_FILE_PATH}`")
        st.caption(
            "When you save this form, the app updates the local .env file and the backend uses those values on the next request."
        )

        with st.form("warehouse_settings_form"):
            bigquery_project = st.text_input(
                "GCP Project",
                value=env_values.get("CFO_PANEL_BIGQUERY_PROJECT", ""),
                help="The GCP project used to run BigQuery queries.",
            )
            mart_project = st.text_input(
                "Mart Project",
                value=env_values.get("CFO_PANEL_MART_PROJECT", ""),
                help="The project that contains the dbt mart tables. Leave empty to reuse the GCP Project value.",
            )
            mart_dataset = st.text_input(
                "Mart Dataset",
                value=env_values.get("CFO_PANEL_MART_DATASET", ""),
                help="Example: cfo_panel_dev",
            )
            bigquery_location = st.selectbox(
                "BigQuery Location",
                options=["US", "EU"],
                index=0
                if env_values.get("CFO_PANEL_BIGQUERY_LOCATION", "US") == "US"
                else 1,
            )
            google_application_credentials = st.text_input(
                "Service Account JSON Path",
                value=env_values.get("GOOGLE_APPLICATION_CREDENTIALS", ""),
                help="Example: /Users/you/keys/my-service-account.json",
            )

            st.markdown("**Source Dataset Settings**")
            ga4_project_id = st.text_input(
                "GA4 Source Project",
                value=env_values.get("CFO_PANEL_GA4_PROJECT_ID", ""),
            )
            ga4_dataset = st.text_input(
                "GA4 Source Dataset",
                value=env_values.get("CFO_PANEL_GA4_DATASET", ""),
            )
            start_date = st.text_input(
                "Start Date",
                value=env_values.get("CFO_PANEL_START_DATE", ""),
                help="Enter the value in YYYYMMDD format.",
            )
            end_date = st.text_input(
                "End Date",
                value=env_values.get("CFO_PANEL_END_DATE", ""),
                help="Enter the value in YYYYMMDD format.",
            )
            assumed_cogs_ratio = st.text_input(
                "Assumed COGS Ratio",
                value=env_values.get("CFO_PANEL_ASSUMED_COGS_RATIO", ""),
                help="Example: 0.58",
            )
            prefer_marts = st.checkbox(
                "Prefer dbt mart tables first",
                value=env_values.get("CFO_PANEL_PREFER_MARTS", "true").lower() == "true",
            )
            allow_source_queries = st.checkbox(
                "Allow GA4 source-query fallback when marts are unavailable",
                value=env_values.get("CFO_PANEL_ALLOW_SOURCE_QUERIES", "true").lower()
                == "true",
            )

            submitted = st.form_submit_button("Save Settings", use_container_width=True)

        if submitted:
            save_editable_env_values(
                {
                    "CFO_PANEL_BIGQUERY_PROJECT": bigquery_project,
                    "CFO_PANEL_MART_PROJECT": mart_project,
                    "CFO_PANEL_MART_DATASET": mart_dataset,
                    "CFO_PANEL_BIGQUERY_LOCATION": bigquery_location,
                    "GOOGLE_APPLICATION_CREDENTIALS": google_application_credentials,
                    "CFO_PANEL_GA4_PROJECT_ID": ga4_project_id,
                    "CFO_PANEL_GA4_DATASET": ga4_dataset,
                    "CFO_PANEL_START_DATE": start_date,
                    "CFO_PANEL_END_DATE": end_date,
                    "CFO_PANEL_ASSUMED_COGS_RATIO": assumed_cogs_ratio,
                    "CFO_PANEL_PREFER_MARTS": prefer_marts,
                    "CFO_PANEL_ALLOW_SOURCE_QUERIES": allow_source_queries,
                }
            )
            st.sidebar.success(".env was updated. Reloading the page to refresh configuration.")
            st.rerun()

        st.markdown("**Active Configuration**")
        st.write(f"GCP Project: `{current_settings.bigquery_project or '-'}`")
        st.write(
            f"Mart: `{current_settings.mart_project or '-'} / {current_settings.mart_dataset or '-'}`"
        )
        st.write(f"Location: `{current_settings.bigquery_location}`")
        st.write(
            f"Credentials: `{current_settings.google_application_credentials or 'not configured'}`"
        )


def main() -> None:
    st.set_page_config(
        page_title="CFO Panel",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()

    st.sidebar.title("Controls")
    render_settings_panel()
    api_base_url = st.sidebar.text_input("API URL", value=DEFAULT_API_BASE_URL)

    bootstrap_client = DashboardClient(api_base_url)
    bootstrap_result = bootstrap_client.fetch_dashboard()
    channel_options = ["all-channels", *bootstrap_result.payload["available_channels"]]

    selected_channel = st.sidebar.selectbox(
        "Channel filter",
        options=channel_options,
        format_func=lambda value: "All channels" if value == "all-channels" else value.title(),
    )

    channel_filter = None if selected_channel == "all-channels" else selected_channel
    result = (
        bootstrap_result
        if channel_filter is None
        else DashboardClient(api_base_url).fetch_dashboard(channel=channel_filter)
    )
    payload = result.payload

    overview = payload["overview"]
    data_source = payload.get("data_source", {})
    data_journey = payload.get("data_journey", {})
    daily_kpis = pd.DataFrame(payload["daily_kpis"])
    channel_performance = pd.DataFrame(payload["channel_performance"])
    recent_orders = pd.DataFrame(payload["recent_orders"])

    render_header(
        result.source_label,
        result.api_available,
        bool(data_source.get("is_live", False)),
    )

    left_col, right_col = st.columns([2.2, 1])
    with left_col:
        st.markdown(
            f"""
            <p class="section-note">
                Selected data range: {payload["data_period"]["start_date"]} - {payload["data_period"]["end_date"]}.
                Filter: {channel_filter or "all channels"}.
                Source detail: {data_source.get("detail", "-")}.
            </p>
            """,
            unsafe_allow_html=True,
        )
    with right_col:
        st.metric("Best day", overview["best_day"] or "-", format_currency(overview["best_day_net_revenue_usd"]))
        st.metric("Top channel", overview["top_channel"] or "-", format_currency(overview["top_channel_net_revenue_usd"]))

    row_one = st.columns(3)
    row_two = st.columns(3)
    with row_one[0]:
        render_metric_card("Net Revenue", format_currency(overview["net_revenue_usd"]), "Revenue after refunds")
    with row_one[1]:
        render_metric_card("Gross Margin", format_currency(overview["gross_margin_usd"]), "Net revenue minus product cost proxy")
    with row_one[2]:
        render_metric_card("Refund Rate", format_percent(overview["refund_rate"]), "Refunds as a share of gross revenue")
    with row_two[0]:
        render_metric_card("Average Order Value", format_currency(overview["aov_usd"]), "Average net revenue per order")
    with row_two[1]:
        render_metric_card("Order Count", f"{overview['total_orders']}", "Total orders in the selected filter")
    with row_two[2]:
        render_metric_card("Active Channels", f"{overview['active_channels']}", "Number of channels generating revenue")

    chart_col, mix_col = st.columns([1.8, 1])
    with chart_col:
        st.subheader("Daily Net Revenue Trend")
        if not daily_kpis.empty:
            line_df = daily_kpis[["order_date", "net_revenue_usd"]].copy()
            line_df["order_date"] = pd.to_datetime(line_df["order_date"])
            line_df = line_df.set_index("order_date")
            st.line_chart(line_df, height=320, use_container_width=True)
    with mix_col:
        st.subheader("Channel Revenue Mix")
        if not channel_performance.empty:
            bar_df = channel_performance[["traffic_source", "net_revenue_usd"]].copy()
            bar_df = bar_df.rename(columns={"traffic_source": "channel"}).set_index("channel")
            st.bar_chart(bar_df, height=320, use_container_width=True)

    tabs = st.tabs(["Data Journey", "Daily KPI", "Channel Performance", "Recent Orders"])

    with tabs[0]:
        st.subheader("Data Journey")
        st.write(data_journey.get("headline", ""))
        st.caption(data_journey.get("summary", ""))

        step_columns = st.columns(4)
        for index, step in enumerate(data_journey.get("steps", [])):
            with step_columns[index % 4]:
                render_journey_card(
                    step.get("stage", ""),
                    step.get("title", ""),
                    step.get("grain", ""),
                    step.get("description", ""),
                    int(step.get("row_count", 0)),
                )

        preview_tabs = st.tabs(["Raw Events", "Staging", "Order-Level", "CFO Mart"])

        with preview_tabs[0]:
            st.caption(
                f"Source: {data_journey.get('source_name', '-')} | {data_journey.get('source_detail', '-')}"
            )
            st.dataframe(
                pd.DataFrame(data_journey.get("source_preview", [])),
                use_container_width=True,
                hide_index=True,
            )

        with preview_tabs[1]:
            st.caption("The cleaned event-level view after type standardization and column renaming.")
            st.dataframe(
                pd.DataFrame(data_journey.get("staging_preview", [])),
                use_container_width=True,
                hide_index=True,
            )

        with preview_tabs[2]:
            st.caption("The order-level model after revenue and refund logic has been applied.")
            st.dataframe(
                pd.DataFrame(data_journey.get("order_preview", [])),
                use_container_width=True,
                hide_index=True,
            )

        with preview_tabs[3]:
            st.caption("A preview of the final KPI table exposed to finance stakeholders.")
            st.dataframe(
                pd.DataFrame(data_journey.get("mart_preview", [])),
                use_container_width=True,
                hide_index=True,
            )

    with tabs[1]:
        st.dataframe(
            daily_kpis,
            use_container_width=True,
            hide_index=True,
            column_config={
                "gross_revenue_usd": st.column_config.NumberColumn("Gross Revenue", format="$%.2f"),
                "refund_amount_usd": st.column_config.NumberColumn("Refunds", format="$%.2f"),
                "net_revenue_usd": st.column_config.NumberColumn("Net Revenue", format="$%.2f"),
                "gross_margin_usd": st.column_config.NumberColumn("Gross Margin", format="$%.2f"),
                "refund_rate": st.column_config.NumberColumn("Refund Rate", format="%.2f"),
                "aov_usd": st.column_config.NumberColumn("AOV", format="$%.2f"),
            },
        )

    with tabs[2]:
        st.dataframe(
            channel_performance,
            use_container_width=True,
            hide_index=True,
            column_config={
                "gross_revenue_usd": st.column_config.NumberColumn("Gross Revenue", format="$%.2f"),
                "refund_amount_usd": st.column_config.NumberColumn("Refunds", format="$%.2f"),
                "net_revenue_usd": st.column_config.NumberColumn("Net Revenue", format="$%.2f"),
                "gross_margin_usd": st.column_config.NumberColumn("Gross Margin", format="$%.2f"),
                "revenue_share": st.column_config.NumberColumn("Revenue Share", format="%.2f"),
                "refund_rate": st.column_config.NumberColumn("Refund Rate", format="%.2f"),
                "aov_usd": st.column_config.NumberColumn("AOV", format="$%.2f"),
            },
        )

    with tabs[3]:
        st.dataframe(
            recent_orders,
            use_container_width=True,
            hide_index=True,
            column_config={
                "gross_revenue_usd": st.column_config.NumberColumn("Gross Revenue", format="$%.2f"),
                "refund_amount_usd": st.column_config.NumberColumn("Refunds", format="$%.2f"),
                "cogs_usd": st.column_config.NumberColumn("COGS", format="$%.2f"),
                "net_revenue_usd": st.column_config.NumberColumn("Net Revenue", format="$%.2f"),
                "gross_margin_usd": st.column_config.NumberColumn("Gross Margin", format="$%.2f"),
            },
        )

    st.caption(
        "The app tries dbt mart tables first. If marts or credentials are not available yet, it temporarily falls back to sample data."
    )


if __name__ == "__main__":
    main()
