from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import streamlit as st


REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
TIME_RANGE_MINUTES = 60
REFRESH_SECONDS = 30
CHART_HEIGHT = 120
WINDOW_EVENTS = {"request_received", "response_sent", "request_failed"}


def load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)


def filter_window(records: list[dict[str, Any]], minutes: int) -> list[dict[str, Any]]:
    timestamps = [parse_timestamp(record.get("ts")) for record in records]
    telemetry_timestamps = [
        timestamp
        for record, timestamp in zip(records, timestamps)
        if timestamp is not None and record.get("event") in WINDOW_EVENTS
    ]
    valid_timestamps = telemetry_timestamps or [
        timestamp for timestamp in timestamps if timestamp is not None
    ]
    if not valid_timestamps:
        return []

    end = max(valid_timestamps)
    start = end - timedelta(minutes=minutes)
    return [
        record
        for record, timestamp in zip(records, timestamps)
        if timestamp is not None and start <= timestamp <= end
    ]


def percentile(values: list[float], percentile_value: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(
        0,
        min(
            len(ordered) - 1,
            round((percentile_value / 100) * len(ordered) + 0.5) - 1,
        ),
    )
    return float(ordered[index])


def numeric_values(records: list[dict[str, Any]], field: str) -> list[float]:
    return [
        float(record[field])
        for record in records
        if isinstance(record.get(field), (int, float))
    ]


def minute_counts(records: list[dict[str, Any]], field: str | None = None) -> dict[str, float]:
    buckets: defaultdict[str, float] = defaultdict(float)
    for record in records:
        timestamp = parse_timestamp(record.get("ts"))
        if timestamp is None:
            continue
        bucket = timestamp.astimezone(timezone.utc).strftime("%H:%M")
        buckets[bucket] += float(record.get(field, 1) if field else 1)
    return dict(sorted(buckets.items()))


def threshold_caption(label: str, operator: str, value: float, unit: str) -> None:
    st.caption(f"Threshold: {label} {operator} {value:g} {unit} | Source: data/logs.jsonl")


def render_dashboard() -> None:
    minutes = st.sidebar.slider("Time range (minutes)", 5, 60, TIME_RANGE_MINUTES)
    if st.sidebar.button("Reload now"):
        st.rerun()
    st.sidebar.caption(f"Auto-refresh: {REFRESH_SECONDS}s")
    st.sidebar.caption(f"Data source: `{LOG_PATH.relative_to(REPO_ROOT)}`")

    records = filter_window(load_records(LOG_PATH), minutes)
    responses = [record for record in records if record.get("event") == "response_sent"]
    requests = [record for record in records if record.get("event") == "request_received"]
    failures = [record for record in records if record.get("event") == "request_failed"]

    st.header("K4-L3A Day 13 Monitoring & LLMOps")
    st.caption(f"Last {minutes} minutes | {len(records)} structured log records | refresh {REFRESH_SECONDS}s")

    latency_values = numeric_values(responses, "latency_ms")
    ttft_values = numeric_values(responses, "ttft_ms")
    traffic_by_minute = minute_counts(requests)
    cost_by_minute = minute_counts(responses, "cost_usd")
    errors_by_type = Counter(
        str(record.get("error_type", "unknown"))
        for record in failures
    )
    retrieval_values = [
        record.get("tool_success")
        for record in responses
        if record.get("tool_success") is not None
    ]
    retrieval_success = (
        sum(value is True for value in retrieval_values) / len(retrieval_values) * 100
        if retrieval_values
        else 0.0
    )

    latency_col, traffic_col, errors_col = st.columns(3)
    with latency_col:
        with st.container(border=True):
            st.subheader("Latency percentiles and TTFT")
            metric_cols = st.columns(4)
            metric_cols[0].metric("P50", f"{percentile(latency_values, 50):.0f} ms")
            metric_cols[1].metric("P95", f"{percentile(latency_values, 95):.0f} ms")
            metric_cols[2].metric("P99", f"{percentile(latency_values, 99):.0f} ms")
            metric_cols[3].metric("TTFT P95", f"{percentile(ttft_values, 95):.0f} ms")
            if latency_values:
                st.line_chart(
                    {"latency_ms": latency_values, "ttft_ms": ttft_values},
                    height=CHART_HEIGHT,
                )
            threshold_caption("P95", "<=", 3000, "ms")

    with traffic_col:
        with st.container(border=True):
            st.subheader("Request traffic")
            request_rate = len(requests) / max(minutes, 1)
            st.metric("Requests", len(requests))
            st.metric("Rate", f"{request_rate:.2f} requests/min")
            if traffic_by_minute:
                st.bar_chart(traffic_by_minute, height=CHART_HEIGHT)
            threshold_caption("Rate", ">=", 1, "requests/min")

    with errors_col:
        with st.container(border=True):
            st.subheader("Error rate and retrieval success")
            error_rate = len(failures) / len(requests) * 100 if requests else 0.0
            metric_cols = st.columns(2)
            metric_cols[0].metric("Error rate", f"{error_rate:.2f}%")
            metric_cols[1].metric("Retrieval success", f"{retrieval_success:.2f}%")
            if errors_by_type:
                st.json(dict(errors_by_type))
            else:
                st.caption("No request failures in the selected window.")
            threshold_caption("Error rate", "<=", 2, "%")

    cost_col, tokens_col, quality_col = st.columns(3)
    with cost_col:
        with st.container(border=True):
            st.subheader("Cost over time")
            total_cost = sum(numeric_values(responses, "cost_usd"))
            st.metric("Total cost", f"${total_cost:.6f}")
            if cost_by_minute:
                st.bar_chart(cost_by_minute, height=CHART_HEIGHT)
            threshold_caption("Total", "<=", 2.5, "USD")

    with tokens_col:
        with st.container(border=True):
            st.subheader("Input and output tokens")
            input_tokens = sum(numeric_values(responses, "tokens_in"))
            output_tokens = sum(numeric_values(responses, "tokens_out"))
            st.metric("Input tokens", f"{input_tokens:,.0f}")
            st.metric("Output tokens", f"{output_tokens:,.0f}")
            if responses:
                st.bar_chart(
                    {"input": [input_tokens], "output": [output_tokens]},
                    height=CHART_HEIGHT,
                )
            threshold_caption("Total", "<=", 50000, "tokens")

    with quality_col:
        with st.container(border=True):
            st.subheader("Quality proxy")
            quality_values = numeric_values(responses, "quality_score")
            quality_mean = sum(quality_values) / len(quality_values) if quality_values else 0.0
            st.metric("Mean quality", f"{quality_mean:.3f}")
            if quality_values:
                st.line_chart({"quality_score": quality_values}, height=CHART_HEIGHT)
            threshold_caption("Mean", ">=", 0.75, "score")

    if not records:
        st.warning("No valid structured logs found in the selected time range.")


st.set_page_config(
    page_title="Day 13 Monitoring & LLMOps",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    [data-testid="stMainBlockContainer"] {
        max-width: 100%;
        padding: 0.65rem 1rem 0.4rem;
    }
    [data-testid="stVerticalBlock"] { gap: 0.35rem; }
    [data-testid="stHorizontalBlock"] { gap: 0.6rem; }
    [data-testid="stMetric"] { padding: 0; }
    [data-testid="stMetricLabel"] { font-size: 0.72rem; }
    [data-testid="stMetricValue"] { font-size: 1.15rem; }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.5rem; }
    h2 {
        font-size: 1.45rem !important;
        line-height: 1.35 !important;
        margin: 0 0 0.25rem !important;
        padding: 0.1rem 0 !important;
    }
    h3 { font-size: 0.95rem !important; margin: 0 !important; }
    .stCaptionContainer { font-size: 0.72rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


if hasattr(st, "fragment"):
    @st.fragment(run_every=f"{REFRESH_SECONDS}s")
    def _render_refreshing_dashboard() -> None:
        render_dashboard()

    _render_refreshing_dashboard()
else:
    render_dashboard()
