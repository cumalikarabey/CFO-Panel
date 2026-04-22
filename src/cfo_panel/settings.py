"""Environment-backed settings for warehouse connectivity."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from dotenv import dotenv_values, load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = PROJECT_ROOT / ".env"
ENV_EXAMPLE_FILE_PATH = PROJECT_ROOT / ".env.example"
EDITABLE_ENV_KEYS = [
    "CFO_PANEL_BIGQUERY_PROJECT",
    "CFO_PANEL_MART_PROJECT",
    "CFO_PANEL_MART_DATASET",
    "CFO_PANEL_BIGQUERY_LOCATION",
    "CFO_PANEL_GA4_PROJECT_ID",
    "CFO_PANEL_GA4_DATASET",
    "CFO_PANEL_START_DATE",
    "CFO_PANEL_END_DATE",
    "CFO_PANEL_ASSUMED_COGS_RATIO",
    "CFO_PANEL_PREFER_MARTS",
    "CFO_PANEL_ALLOW_SOURCE_QUERIES",
    "GOOGLE_APPLICATION_CREDENTIALS",
]


def reload_dotenv(env_path: Path | None = None) -> None:
    load_dotenv(dotenv_path=env_path or ENV_FILE_PATH, override=True)


reload_dotenv()


def _stringify_env_value(value: object | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _serialize_env_value(value: object | None) -> str:
    serialized = _stringify_env_value(value)
    if serialized == "":
        return ""
    if any(character.isspace() for character in serialized) or any(
        token in serialized for token in ['#', '"', "'"]
    ):
        escaped = serialized.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return serialized


def _example_env_defaults(example_path: Path | None = None) -> dict[str, str]:
    resolved_path = example_path or ENV_EXAMPLE_FILE_PATH
    if not resolved_path.exists():
        return {}
    return {
        key: _stringify_env_value(value)
        for key, value in dotenv_values(resolved_path).items()
        if key is not None
    }


def get_editable_env_values(
    env_path: Path | None = None,
    example_path: Path | None = None,
) -> dict[str, str]:
    resolved_env_path = env_path or ENV_FILE_PATH
    current_values = (
        {
            key: _stringify_env_value(value)
            for key, value in dotenv_values(resolved_env_path).items()
            if key is not None
        }
        if resolved_env_path.exists()
        else {}
    )
    defaults = _example_env_defaults(example_path=example_path)

    values: dict[str, str] = {}
    for key in EDITABLE_ENV_KEYS:
        if key in current_values:
            values[key] = current_values[key]
        elif key in os.environ:
            values[key] = _stringify_env_value(os.getenv(key))
        else:
            values[key] = defaults.get(key, "")
    return values


def save_editable_env_values(
    values: Mapping[str, object | None],
    env_path: Path | None = None,
    example_path: Path | None = None,
) -> None:
    resolved_env_path = env_path or ENV_FILE_PATH
    existing_values = (
        {
            key: _stringify_env_value(value)
            for key, value in dotenv_values(resolved_env_path).items()
            if key is not None
        }
        if resolved_env_path.exists()
        else {}
    )
    defaults = _example_env_defaults(example_path=example_path)

    merged_values = {**defaults, **existing_values}
    for key in EDITABLE_ENV_KEYS:
        if key not in merged_values:
            merged_values[key] = ""
    for key, value in values.items():
        merged_values[key] = _stringify_env_value(value)

    ordered_keys = [key for key in EDITABLE_ENV_KEYS if key in merged_values]
    extra_keys = sorted(key for key in merged_values if key not in EDITABLE_ENV_KEYS)
    lines = [
        f"{key}={_serialize_env_value(merged_values[key])}"
        for key in [*ordered_keys, *extra_keys]
    ]

    resolved_env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    reload_dotenv(env_path=resolved_env_path)


def _env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError:
        return default


@dataclass(frozen=True)
class WarehouseSettings:
    bigquery_project: str | None
    mart_project: str | None
    mart_dataset: str | None
    bigquery_location: str
    ga4_project_id: str
    ga4_dataset: str
    start_date: str
    end_date: str
    assumed_cogs_ratio: float
    prefer_marts: bool
    allow_source_queries: bool
    google_application_credentials: str | None

    @classmethod
    def from_env(cls) -> "WarehouseSettings":
        reload_dotenv()
        bigquery_project = os.getenv("CFO_PANEL_BIGQUERY_PROJECT")
        mart_project = os.getenv("CFO_PANEL_MART_PROJECT") or bigquery_project
        mart_dataset = os.getenv("CFO_PANEL_MART_DATASET") or os.getenv(
            "CFO_PANEL_BIGQUERY_DATASET"
        )

        return cls(
            bigquery_project=bigquery_project or None,
            mart_project=mart_project or None,
            mart_dataset=mart_dataset or None,
            bigquery_location=os.getenv("CFO_PANEL_BIGQUERY_LOCATION", "US"),
            ga4_project_id=os.getenv("CFO_PANEL_GA4_PROJECT_ID", "bigquery-public-data"),
            ga4_dataset=os.getenv(
                "CFO_PANEL_GA4_DATASET", "ga4_obfuscated_sample_ecommerce"
            ),
            start_date=os.getenv("CFO_PANEL_START_DATE", "20201101"),
            end_date=os.getenv("CFO_PANEL_END_DATE", "20210131"),
            assumed_cogs_ratio=_env_float("CFO_PANEL_ASSUMED_COGS_RATIO", 0.58),
            prefer_marts=_env_bool("CFO_PANEL_PREFER_MARTS", True),
            allow_source_queries=_env_bool("CFO_PANEL_ALLOW_SOURCE_QUERIES", True),
            google_application_credentials=os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            or None,
        )

    @property
    def has_mart_target(self) -> bool:
        return bool(self.mart_project and self.mart_dataset)

    @property
    def can_query_bigquery(self) -> bool:
        return self.has_mart_target or self.allow_source_queries

    def mart_table(self, table_name: str) -> str:
        if not self.has_mart_target:
            raise ValueError("Mart project and dataset must be configured first.")
        return f"`{self.mart_project}.{self.mart_dataset}.{table_name}`"
