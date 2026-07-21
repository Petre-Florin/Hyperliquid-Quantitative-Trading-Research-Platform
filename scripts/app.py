"""Interactive backtest + live dashboard. Run with: streamlit run scripts/app.py"""

import asyncio
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

from backtest_core import discover_available_data, make_strategy, run_backtest
from state_store import get_equity_history, get_recent_trades, get_strategy_names, init_db
from strategy_registry import discover_strategies

st.set_page_config(page_title="Strategy Backtester", layout="wide", page_icon="\U0001F4CA")

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1100px; }
    .stApp { background: radial-gradient(circle at 15% 10%, #1a1c2c 0%, #0d0e17 55%); }

    h1 { font-size: 1.6rem !important; font-weight: 800;
         background: linear-gradient(135deg, #7b5cff, #4facfe);
         -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.2rem; }
    h2, h3 { font-size: 1.05rem !important; font-weight: 700; color: #ddd; margin-top: 0.4rem; }

    section[data-testid="stSidebar"] {
        background: rgba(255,255,255,0.03);
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    .glass-card {
        background: rgba(255,255,255,0.035);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 12px;
        padding: 0.6rem 0.8rem 0.4rem 0.8rem;
    }
    div[data-testid="stMetricValue"] { font-size: 1.05rem; }
    div[data-testid="stMetricLabel"] { font-size: 0.75rem; opacity: 0.75; }
    div[data-testid="stMetricDelta"] { font-size: 0.75rem; }

    .stButton > button {
        background: linear-gradient(135deg, #7b5cff 0%, #4facfe 100%);
        color: white; border: none; border-radius: 8px;
        padding: 0.45rem 1.1rem; font-weight: 600; font-size: 0.85rem;
    }
    .stButton > button:hover { color: white; }

    .stCaption, .stMarkdown p { font-size: 0.82rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

plt.rcParams.update({
    "figure.facecolor": "#0d0e17", "axes.facecolor": "#12131f", "axes.edgecolor": "#333",
    "axes.labelcolor": "#ccc", "xtick.color": "#999", "ytick.color": "#999",
    "text.color": "#ddd", "grid.color": "#222", "legend.facecolor": "#1a1c2c",
    "legend.edgecolor": "#333", "font.size": 8,
})

init_db()

st.title("Hyperliquid Strategy Backtester")
st.caption("Runs your real strategy/risk/execution pipeline against historical data — no separate backtest logic.")

available_data = discover_available_data()
strategy_registry = discover_strategies()

with st.sidebar:
    st.subheader("Setup")
    symbol = st.text_input("Symbol", value=next(iter(available_data), "BTC"))

    symbol_intervals = available_data.get(symbol, [])
    if not symbol_intervals:
        st.warning(f"No data for {symbol}. Run:\n\n`python scripts/fetch_historical.py {symbol}`")

    selected_strategies = st.multiselect(
        "Strategies",
        options=list(strategy_registry.keys()),
        default=list(strategy_registry.keys())[:1],
    )
    selected_intervals = st.multiselect(
        "Intervals", options=symbol_intervals, default=symbol_intervals[:1]
    )

    run_clicked = st.button("\u25B6 Run backtest", type="primary", use_container_width=True)

    with st.expander("Available data"):
        if not available_data:
            st.caption("None yet — run fetch_historical.py")
        for sym, ivs in available_data.items():
            st.caption(f"**{sym}**: {', '.join(ivs)}")

    with st.expander("Discovered strategies"):
        for name in strategy_registry:
            st.caption(f"\u2022 {name}")
        st.caption("Drop a new file in `src/strategies/` (see `_template.py`) — it appears here automatically. Editing an existing strategy file needs a restart to take effect.")


def make_label(strat: str, interval: str, multi_strat: bool, multi_interval: bool) -> str:
    if multi_strat and multi_interval:
        return f"{strat}/{interval}"
    if multi_strat:
        return strat
    if multi_interval:
        return interval
    return f"{strat} \u00b7 {interval}"


main_tab_backtest, main_tab_live = st.tabs(["Backtest", "Live"])

with main_tab_backtest:
    if run_clicked:
        if not selected_strategies or not selected_intervals:
            st.warning("Pick at least one strategy and one interval.")
        else:
            multi_strat = len(selected_strategies) > 1
            multi_interval = len(selected_intervals) > 1

            combos = [(s, i) for s in selected_strategies for i in selected_intervals]
            results = []
            progress = st.progress(0.0)

            for idx, (strat_name, interval) in enumerate(combos):
                try:
                    result = asyncio.run(run_backtest(symbol, interval, [make_strategy(strat_name)]))
                    result["label"] = make_label(strat_name, interval, multi_strat, multi_interval)
                    results.append(result)
                except FileNotFoundError:
                    st.error(f"No data for {symbol} {interval}.")
                progress.progress((idx + 1) / len(combos))
            progress.empty()

            if results:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.subheader("Summary")
                cols_per_row = 4
                for row_start in range(0, len(results), cols_per_row):
                    row_results = results[row_start: row_start + cols_per_row]
                    cols = st.columns(len(row_results))
                    for col, r in zip(cols, row_results):
                        with col:
                            st.metric(r["label"], f"${r['final_value']:.2f}", delta=f"{r['net_pnl']:.2f}")
                            st.caption(
                                f"{r['trade_count']} trades \u00b7 ${r['total_fees']:.2f} fees \u00b7 "
                                f"DD {r['max_drawdown_pct']:.1f}%"
                            )
                st.markdown("</div>", unsafe_allow_html=True)

                if len(results) > 1:
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    st.subheader("Comparison (normalized % return)")
                    fig, ax = plt.subplots(figsize=(9, 3.2))
                    colors = ["#4facfe", "#f6ad55", "#68d391", "#fc8181", "#b794f4", "#f687b3"]
                    for i, r in enumerate(results):
                        n = r["num_ticks"]
                        x_pct = [j / (n - 1) * 100 for j in range(n)]
                        pct_return = [(row["equity"] - 10000.0) / 10000.0 * 100 for row in r["equity_curve"]]
                        ax.plot(x_pct, pct_return, label=r["label"], linewidth=1.2, color=colors[i % len(colors)])
                    ax.axhline(0.0, color="#555", linestyle="--", linewidth=0.7)
                    ax.set_xlabel("Progress (%)", fontsize=8)
                    ax.set_ylabel("Return (%)", fontsize=8)
                    ax.legend(fontsize=7, title_fontsize=7)
                    ax.grid(alpha=0.15)
                    st.pyplot(fig)
                    st.markdown("</div>", unsafe_allow_html=True)

                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.subheader("Individual runs")
                tabs = st.tabs([r["label"] for r in results])
                for tab, r in zip(tabs, results):
                    with tab:
                        steps = [row["step"] for row in r["equity_curve"]]
                        prices_list = [row["price"] for row in r["equity_curve"]]
                        equity = [row["equity"] for row in r["equity_curve"]]
                        buys = [(row["step"], row["price"]) for row in r["equity_curve"] if row["trade"] == "BUY"]
                        sells = [(row["step"], row["price"]) for row in r["equity_curve"] if row["trade"] == "SELL"]

                        fig2, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 4.5), sharex=True)
                        ax1.plot(steps, prices_list, color="#ddd", linewidth=0.7, label=f"{symbol} price")
                        if buys:
                            ax1.scatter(*zip(*buys), color="#68d391", marker="^", s=22, label="BUY", zorder=5)
                        if sells:
                            ax1.scatter(*zip(*sells), color="#fc8181", marker="v", s=22, label="SELL", zorder=5)
                        ax1.legend(fontsize=7)
                        ax1.grid(alpha=0.15)
                        ax2.plot(steps, equity, color="#4facfe", linewidth=1.0, label="Equity")
                        ax2.axhline(10000.0, color="#555", linestyle="--", linewidth=0.7)
                        ax2.legend(fontsize=7)
                        ax2.grid(alpha=0.15)
                        st.pyplot(fig2)

                        m1, m2, m3 = st.columns(3)
                        m1.metric("Max drawdown", f"{r['max_drawdown_pct']:.2f}%")
                        m2.metric("Risk ratio*", f"{r['risk_ratio']:.3f}")
                        m3.metric("Trades", r["trade_count"])
                st.caption(
                    "*Risk ratio = mean tick return / std dev of tick returns \u2014 a relative, "
                    "unannualized comparison metric, not a standard annualized Sharpe ratio."
                )
                st.markdown("</div>", unsafe_allow_html=True)

with main_tab_live:
    st.subheader("Live trading")

    strategy_names = get_strategy_names()
    if not strategy_names:
        st.info("No live data yet — start the engine with `python main.py` and come back.")
    else:
        selected = st.selectbox("Strategy", ["All"] + strategy_names)
        auto_refresh = st.checkbox("Auto-refresh every 5s", value=False)

        if selected == "All":
            fig, ax = plt.subplots(figsize=(9, 3.5))
            for name in strategy_names:
                rows = get_equity_history(name)
                if rows:
                    ax.plot([r["id"] for r in rows], [r["equity"] for r in rows], label=name, linewidth=1.2)
            ax.set_xlabel("Snapshot #", fontsize=8)
            ax.set_ylabel("Equity ($)", fontsize=8)
            ax.legend(fontsize=7)
            ax.grid(alpha=0.15)
            st.pyplot(fig)
        else:
            history = get_equity_history(selected)
            if history:
                fig, ax = plt.subplots(figsize=(9, 3.5))
                ax.plot([r["id"] for r in history], [r["equity"] for r in history], color="#4facfe", linewidth=1.2)
                ax.set_xlabel("Snapshot #", fontsize=8)
                ax.set_ylabel("Equity ($)", fontsize=8)
                ax.grid(alpha=0.15)
                st.pyplot(fig)

        st.subheader("Recent trades")
        trades = get_recent_trades(limit=50)
        if trades:
            st.dataframe(trades, use_container_width=True)
        else:
            st.caption("No trades yet.")

        if auto_refresh:
            time.sleep(5)
            st.rerun()