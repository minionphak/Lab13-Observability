"""Build a 6-panel observability dashboard from /metrics and data/logs.jsonl."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

BASE_URL = "http://localhost:8000"
LOG_PATH = Path("data/logs.jsonl")
OUT_PATH = Path("output/dashboard.png")


def fetch_metrics() -> dict:
    try:
        r = httpx.get(f"{BASE_URL}/metrics", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Error fetching /metrics: {e}")
        sys.exit(1)


def load_logs() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    records = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def extract_latency_series(logs: list[dict]) -> list[float]:
    return [
        r["latency_ms"]
        for r in logs
        if r.get("event") == "response_sent" and "latency_ms" in r
    ]


def extract_cost_series(logs: list[dict]) -> list[float]:
    costs = []
    running = 0.0
    for r in logs:
        if r.get("event") == "response_sent" and "cost_usd" in r:
            running += r["cost_usd"]
            costs.append(running)
    return costs


def extract_quality_series(logs: list[dict]) -> list[float]:
    # quality_score is on AgentResult, not in logs — approximate from cost proxy
    # fall back to empty; panel will show static avg from /metrics
    return []


def build(metrics: dict, logs: list[dict]) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    latency_series = extract_latency_series(logs)
    cost_series = extract_cost_series(logs)

    fig = plt.figure(figsize=(16, 10))
    fig.suptitle("Observability Dashboard — Lab 13", fontsize=16, fontweight="bold", y=0.98)
    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

    # ── Panel 1: Request Traffic ──────────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    traffic = metrics.get("traffic", 0)
    errors = sum(metrics.get("error_breakdown", {}).values())
    ax1.bar(["Success", "Errors"], [traffic - errors, errors], color=["#4CAF50", "#F44336"])
    ax1.set_title("Panel 1 · Request Traffic")
    ax1.set_ylabel("Requests")
    for bar in ax1.patches:
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                 str(int(bar.get_height())), ha="center", va="bottom", fontsize=10)

    # ── Panel 2: Latency Distribution (P50 / P95 / P99) ──────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    p_labels = ["P50", "P95", "P99"]
    p_values = [
        metrics.get("latency_p50", 0),
        metrics.get("latency_p95", 0),
        metrics.get("latency_p99", 0),
    ]
    colors = ["#2196F3", "#FF9800", "#F44336"]
    bars = ax2.bar(p_labels, p_values, color=colors)
    ax2.set_title("Panel 2 · Latency Distribution (ms)")
    ax2.set_ylabel("Latency (ms)")
    ax2.axhline(5000, color="red", linestyle="--", linewidth=1, label="SLO 5000ms")
    ax2.legend(fontsize=8)
    for bar, val in zip(bars, p_values):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 10,
                 f"{val:.0f}", ha="center", va="bottom", fontsize=9)

    # ── Panel 3: Error Breakdown ──────────────────────────────────────────────
    ax3 = fig.add_subplot(gs[0, 2])
    error_bd = metrics.get("error_breakdown", {})
    if error_bd:
        ax3.pie(list(error_bd.values()), labels=list(error_bd.keys()),
                autopct="%1.0f%%", startangle=90)
        ax3.set_title("Panel 3 · Error Breakdown")
    else:
        ax3.text(0.5, 0.5, "No errors recorded", ha="center", va="center",
                 fontsize=12, color="green", transform=ax3.transAxes)
        ax3.set_title("Panel 3 · Error Breakdown")
        ax3.axis("off")

    # ── Panel 4: Cost Tracking ────────────────────────────────────────────────
    ax4 = fig.add_subplot(gs[1, 0])
    if cost_series:
        ax4.plot(range(1, len(cost_series) + 1), cost_series, color="#9C27B0", linewidth=1.5)
        ax4.fill_between(range(1, len(cost_series) + 1), cost_series, alpha=0.15, color="#9C27B0")
        ax4.set_xlabel("Request #")
    else:
        total = metrics.get("total_cost_usd", 0)
        avg = metrics.get("avg_cost_usd", 0)
        ax4.bar(["Total Cost (USD)", "Avg/Request (USD)"], [total, avg], color=["#9C27B0", "#CE93D8"])
    ax4.set_title("Panel 4 · Cost Tracking (USD)")
    ax4.set_ylabel("Cumulative Cost (USD)")

    # ── Panel 5: Token Usage ──────────────────────────────────────────────────
    ax5 = fig.add_subplot(gs[1, 1])
    tokens_in = metrics.get("tokens_in_total", 0)
    tokens_out = metrics.get("tokens_out_total", 0)
    ax5.bar(["Input Tokens", "Output Tokens"], [tokens_in, tokens_out],
            color=["#03A9F4", "#FF5722"])
    ax5.set_title("Panel 5 · Token Usage")
    ax5.set_ylabel("Total Tokens")
    for bar in ax5.patches:
        ax5.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(tokens_in, tokens_out) * 0.01,
                 f"{int(bar.get_height()):,}", ha="center", va="bottom", fontsize=9)

    # ── Panel 6: Quality Score ────────────────────────────────────────────────
    ax6 = fig.add_subplot(gs[1, 2])
    quality_avg = metrics.get("quality_avg", 0.0)
    gauge_color = "#4CAF50" if quality_avg >= 0.7 else "#FF9800" if quality_avg >= 0.5 else "#F44336"
    ax6.barh(["Avg Quality Score"], [quality_avg], color=gauge_color, height=0.4)
    ax6.barh(["Avg Quality Score"], [1.0], color="#E0E0E0", height=0.4, zorder=0)
    ax6.set_xlim(0, 1.0)
    ax6.axvline(0.6, color="red", linestyle="--", linewidth=1.2, label="Threshold 0.6")
    ax6.text(quality_avg + 0.02, 0, f"{quality_avg:.2f}", va="center", fontsize=14, fontweight="bold")
    ax6.set_title("Panel 6 · Response Quality Score")
    ax6.legend(fontsize=8)
    ax6.set_xlabel("Score (0–1)")

    plt.savefig(OUT_PATH, dpi=150, bbox_inches="tight")
    print(f"Dashboard saved → {OUT_PATH.resolve()}")
    plt.show()


if __name__ == "__main__":
    print("Fetching metrics from /metrics ...")
    metrics = fetch_metrics()
    print(json.dumps(metrics, indent=2))
    print("\nLoading logs ...")
    logs = load_logs()
    print(f"Loaded {len(logs)} log records.")
    build(metrics, logs)
