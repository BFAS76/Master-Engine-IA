import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Fibonacci ratios: (XD_ratio, label)
_HARMONIC_RATIOS = {
    "Gartley": 0.618,
    "Cypher":  0.786,
    "Bat":     0.886,
    "Shark":   1.130,
    "Crab":    1.618,
}


def _identify_harmonic(x, a, b, c, d) -> tuple[str, float] | None:
    """
    Check XABCD points against known harmonic Fibonacci ratios.
    Returns (pattern_name, completion_pct) or None.
    """
    xa = abs(a - x)
    xd = abs(d - x)
    if xa < 1e-10:
        return None
    ratio = xd / xa
    best_name, best_diff = None, 0.20  # tolerance
    for name, target in _HARMONIC_RATIOS.items():
        diff = abs(ratio - target)
        if diff < best_diff:
            best_diff = diff
            best_name = name
    if best_name is None:
        return None
    completion = max(0.0, 100.0 - best_diff * 500)
    return best_name, completion


def _build_xabcd(df: pd.DataFrame, highs_idx: np.ndarray, lows_idx: np.ndarray) -> list | None:
    """
    Build XABCD harmonic points from significant alternating swing highs/lows.
    Filters minor swings: only keeps swings with amplitude > 1.5 * ATR.
    """
    atr_mean = float(df["ATR"].dropna().mean()) if "ATR" in df.columns else 0.0
    min_move = atr_mean * 0.5

    highs = [(i, float(df["High"].iloc[i]), "H") for i in highs_idx if i < len(df)]
    lows  = [(i, float(df["Low"].iloc[i]),  "L") for i in lows_idx  if i < len(df)]
    swings = sorted(highs + lows, key=lambda s: s[0])

    # Strict alternation
    alternating: list = []
    for pos, price, kind in swings:
        if not alternating or alternating[-1][2] != kind:
            alternating.append((pos, price, kind))

    # Filter: only keep swings where amplitude to previous swing >= min_move
    if min_move > 0:
        significant: list = []
        for i, (pos, price, kind) in enumerate(alternating):
            if i == 0:
                significant.append((pos, price, kind))
            else:
                prev_price = significant[-1][1] if significant else alternating[i-1][1]
                if abs(price - prev_price) >= min_move:
                    significant.append((pos, price, kind))
        alternating = significant

    if len(alternating) < 5:
        return None

    labels = ["X", "A", "B", "C", "D"]
    best_pts   = None
    best_score = 99.0

    candidates = alternating[-10:]
    for start in range(len(candidates) - 4):
        window = candidates[start:start + 5]
        prices = [p for _, p, _ in window]
        result = _identify_harmonic(*prices)
        if result:
            _, completion = result
            score = 100 - completion
            if score < best_score:
                best_score = score
                best_pts   = window

    if best_pts is None:
        best_pts = alternating[-5:]

    return [(p[0], p[1], lbl) for p, lbl in zip(best_pts, labels)]


def build_chart(
    df: pd.DataFrame,
    stats: dict,
    sl: float,
    tp1: float,
    tp2: float,
    tp3: float,
    direcao: str,
    ativo_label: str,
    highs_idx: np.ndarray | None = None,
    lows_idx: np.ndarray | None = None,
) -> go.Figure:
    """Candlestick chart with all analysis overlays."""

    # Build XABCD from full df BEFORE tailing (positions are in full-df space)
    xabcd_result = None
    if highs_idx is not None and lows_idx is not None:
        xabcd_result = _build_xabcd(df, highs_idx, lows_idx)

    # Use last 200 candles max for readability
    n_full = len(df)
    df = df.tail(200).copy()
    tail_offset = n_full - len(df)  # absolute pos = tail_offset + tail_pos
    idx = df.index

    def abs_to_idx(pos: int):
        """Convert absolute df position to DatetimeIndex timestamp."""
        tail_pos = pos - tail_offset
        if 0 <= tail_pos < len(idx):
            return idx[tail_pos]
        return None

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.60, 0.20, 0.20],
        vertical_spacing=0.02,
        subplot_titles=(f"{ativo_label} — Análise Técnica BFAS76", "RSI (14)", "Volume"),
    )

    # --- CANDLESTICKS ---
    fig.add_trace(go.Candlestick(
        x=idx,
        open=df["Open"], high=df["High"],
        low=df["Low"],  close=df["Close"],
        name="Preço",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
        increasing_fillcolor="#26a69a",
        decreasing_fillcolor="#ef5350",
    ), row=1, col=1)

    # --- EMA 200 ---
    fig.add_trace(go.Scatter(
        x=idx, y=df["EMA_200"],
        name="EMA 200",
        line=dict(color="#f7c948", width=1.5),
    ), row=1, col=1)

    # --- SMA 20 ---
    fig.add_trace(go.Scatter(
        x=idx, y=df["SMA_20"],
        name="SMA 20",
        line=dict(color="#7b61ff", width=1, dash="dot"),
    ), row=1, col=1)

    # --- PADRÕES HARMÓNICOS ---
    xabcd = xabcd_result
    if xabcd:
            # Convert absolute positions to timestamps; skip points outside tail window
            ts_coords = [abs_to_idx(pos) for pos, _, _ in xabcd]
            prices     = [p for _, p, _ in xabcd]
            # Only draw if all 5 points are visible in tail
            if all(ts is not None for ts in ts_coords):
                result  = _identify_harmonic(*prices)
                pname   = result[0] if result else "Harmónico"
                is_bearish_pat = prices[4] > prices[0]
                h_color = "#ef5350" if is_bearish_pat else "#26a69a"

                # Zigzag lines X→A→B→C→D
                fig.add_trace(go.Scatter(
                    x=ts_coords, y=prices,
                    line=dict(color=h_color, width=1.5),
                    name=pname,
                    mode="lines",
                    showlegend=True,
                ), row=1, col=1)

                # Fibonacci ratio on each leg midpoint
                legs = [(0,1,"XA"), (1,2,"AB"), (2,3,"BC"), (3,4,"CD")]
                leg_lengths = [abs(prices[b] - prices[a]) for a, b, _ in legs]
                for i, (a, b, leg_name) in enumerate(legs):
                    prev_len = leg_lengths[i-1] if i > 0 else leg_lengths[0]
                    ratio = leg_lengths[i] / prev_len if prev_len > 1e-10 else 0
                    pa, pb = xabcd[a][0], xabcd[b][0]
                    mid_pos = (pa + pb) // 2
                    mid_ts  = abs_to_idx(mid_pos) or ts_coords[a]
                    mid_price = (prices[a] + prices[b]) / 2
                    offset = (df["ATR"].iloc[-1] * 0.3) if "ATR" in df.columns else 0
                fig.add_annotation(
                    x=mid_ts, y=mid_price + offset,
                    text=f"{ratio:.3f}",
                    showarrow=False,
                    font=dict(color=h_color, size=9, family="Consolas"),
                    bgcolor="rgba(22,27,34,0.8)",
                    bordercolor=h_color,
                    borderwidth=1,
                    row=1, col=1,
                )

                # Point labels X A B C D in boxes
                for xi, (pos, price, lbl) in enumerate(xabcd):
                    ts = abs_to_idx(pos)
                    if ts is None:
                        continue
                    above = (xi == 0) or (price >= prices[xi - 1])
                    yshift = 14 if above else -14
                    fig.add_annotation(
                        x=ts, y=price,
                        text=f"<b>{lbl}</b>",
                        showarrow=False,
                        font=dict(color="#ffffff", size=11, family="Consolas"),
                        bgcolor=h_color,
                        bordercolor=h_color,
                        borderwidth=1,
                        yshift=yshift,
                        row=1, col=1,
                    )

                # Pattern name + completion at D
                if result:
                    pct = result[1]
                    dpos, dprice, _ = xabcd[-1]
                    d_ts = abs_to_idx(dpos)
                    if d_ts is not None:
                        fig.add_annotation(
                            x=d_ts, y=dprice,
                            text=f"<b>{pname} {pct:.0f}%</b>",
                            showarrow=True, arrowhead=2,
                            arrowcolor=h_color,
                            font=dict(color=h_color, size=10, family="Consolas"),
                            bgcolor="#161b22",
                            bordercolor=h_color,
                            ax=50, ay=-35,
                            row=1, col=1,
                        )

    # --- ORDER BLOCKS (SMC corrected) ---
    # Bullish OB = bearish candle before bullish impulse → support zone below price
    # Bearish OB = bullish candle before bearish impulse → resistance zone above price
    ob_sets = []
    if "BullishOB" in df.columns:
        for ts, row in df[df["BullishOB"]].tail(3).iterrows():
            ob_sets.append((ts, row, "Bullish OB", "rgba(38,166,154,0.20)", "#26a69a"))
    if "BearishOB" in df.columns:
        for ts, row in df[df["BearishOB"]].tail(3).iterrows():
            ob_sets.append((ts, row, "Bearish OB", "rgba(239,83,80,0.20)", "#ef5350"))

    for ts, row, label, color, border in ob_sets:
        x_end = idx[-1]
        body_top = max(row["Open"], row["Close"])
        body_bot = min(row["Open"], row["Close"])
        fig.add_shape(
            type="rect",
            x0=ts, x1=x_end,
            y0=body_bot, y1=body_top,
            fillcolor=color,
            line=dict(color=border, width=1, dash="dot"),
            row=1, col=1,
        )
        fig.add_annotation(
            x=ts, y=body_top if "Bearish" in label else body_bot,
            text=label,
            showarrow=False,
            font=dict(size=9, color=border),
            xanchor="left",
            row=1, col=1,
        )

    # --- SL / TP LINES ---
    close_last = float(df["Close"].iloc[-1])
    lines = [
        (sl,  "#ef5350", "SL",  "dash"),
        (tp1, "#26a69a", "TP1", "dot"),
        (tp2, "#26a69a", "TP2", "dot"),
        (tp3, "#26a69a", "TP3", "dashdot"),
    ]
    for price, color, label, dash in lines:
        fig.add_hline(
            y=price,
            line=dict(color=color, width=1, dash=dash),
            annotation_text=f"{label}: {price:.4f}",
            annotation_font=dict(color=color, size=10),
            annotation_position="right",
            row=1, col=1,
        )

    # --- ENTRY SIGNAL ARROW ---
    arrow_y  = float(df["Low"].iloc[-1])  * 0.9990 if direcao == "COMPRA" else float(df["High"].iloc[-1]) * 1.0010
    arrow_ay = 40 if direcao == "COMPRA" else -40
    fig.add_annotation(
        x=idx[-1], y=arrow_y,
        text="▲ COMPRA" if direcao == "COMPRA" else "▼ VENDA",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#26a69a" if direcao == "COMPRA" else "#ef5350",
        font=dict(
            color="#26a69a" if direcao == "COMPRA" else "#ef5350",
            size=12, family="Consolas",
        ),
        ay=arrow_ay, ax=0,
        row=1, col=1,
    )

    # --- RSI ---
    fig.add_trace(go.Scatter(
        x=idx, y=df["RSI"],
        name="RSI",
        line=dict(color="#58a6ff", width=1.5),
    ), row=2, col=1)
    for level, color in [(70, "rgba(239,83,80,0.3)"), (30, "rgba(38,166,154,0.3)")]:
        fig.add_hline(y=level, line=dict(color=color, dash="dot", width=1), row=2, col=1)
    # RSI overbought/oversold fill
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(239,83,80,0.05)", line_width=0, row=2, col=1)
    fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(38,166,154,0.05)", line_width=0, row=2, col=1)

    # --- VOLUME ---
    colors = ["#26a69a" if c >= o else "#ef5350"
              for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(
        x=idx, y=df["Volume"],
        name="Volume",
        marker_color=colors,
        showlegend=False,
    ), row=3, col=1)

    # --- LAYOUT ---
    fig.update_layout(
        height=750,
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0d1117",
        font=dict(color="#d1d4dc", family="Consolas"),
        xaxis_rangeslider_visible=False,
        legend=dict(
            bgcolor="#161b22",
            bordercolor="#30363d",
            borderwidth=1,
            font=dict(size=11),
        ),
        margin=dict(l=10, r=120, t=40, b=10),
    )
    # Grid styling for all rows
    for i in range(1, 4):
        fig.update_xaxes(
            gridcolor="#1f2937", zeroline=False,
            showspikes=True, spikecolor="#58a6ff", spikemode="across",
            row=i, col=1,
        )
        fig.update_yaxes(
            gridcolor="#1f2937", zeroline=False,
            showspikes=True, spikecolor="#58a6ff",
            row=i, col=1,
        )

    return fig
