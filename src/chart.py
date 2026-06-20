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
    Build alternating swing points for XABCD harmonic pattern.
    Returns list of (index_position, price, label) or None if not enough swings.
    """
    # Merge highs and lows, sort by position
    highs = [(i, float(df["High"].iloc[i]), "H") for i in highs_idx if i < len(df)]
    lows  = [(i, float(df["Low"].iloc[i]),  "L") for i in lows_idx  if i < len(df)]
    swings = sorted(highs + lows, key=lambda x: x[0])

    # Keep only alternating H/L
    alternating = []
    for pos, price, kind in swings:
        if not alternating or alternating[-1][2] != kind:
            alternating.append((pos, price, kind))

    if len(alternating) < 5:
        return None

    # Take last 5 alternating swings as X A B C D
    pts = alternating[-5:]
    labels = ["X", "A", "B", "C", "D"]
    return [(p[0], p[1], lbl) for p, lbl in zip(pts, labels)]


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

    # Use last 200 candles max for readability
    df = df.tail(200).copy()
    idx = df.index

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
    if highs_idx is not None and lows_idx is not None:
        xabcd = _build_xabcd(df, highs_idx, lows_idx)
        if xabcd:
            prices = [p for _, p, _ in xabcd]
            result = _identify_harmonic(*prices)
            h_color = "#f7c948"
            # Draw zigzag lines X→A→B→C→D
            x_coords = [idx[pos] for pos, _, _ in xabcd]
            y_coords = [p for _, p, _ in xabcd]
            fig.add_trace(go.Scatter(
                x=x_coords, y=y_coords,
                mode="lines",
                name="Harmónico",
                line=dict(color=h_color, width=1.5, dash="dot"),
                showlegend=True,
            ), row=1, col=1)
            # Labels at each point
            for xi, (pos, price, lbl) in enumerate(xabcd):
                is_high = price == max(y_coords[max(0, xi-1):xi+2])
                fig.add_annotation(
                    x=idx[pos], y=price,
                    text=lbl,
                    showarrow=False,
                    font=dict(color=h_color, size=11, family="Consolas"),
                    yshift=10 if (xi == 0 or price >= y_coords[xi-1]) else -10,
                    row=1, col=1,
                )
            # Pattern name label at D point
            if result:
                pname, pct = result
                dpos, dprice, _ = xabcd[-1]
                fig.add_annotation(
                    x=idx[dpos], y=dprice,
                    text=f"{pname} {pct:.0f}%",
                    showarrow=True,
                    arrowhead=1,
                    arrowcolor=h_color,
                    font=dict(color=h_color, size=10, family="Consolas"),
                    bgcolor="#161b22",
                    bordercolor=h_color,
                    ax=40, ay=-30,
                    row=1, col=1,
                )

    # --- ORDER BLOCKS ---
    ob_df = df[df["OB"]].tail(5)
    for i, (ts, row) in enumerate(ob_df.iterrows()):
        is_bull = row["Close"] > row["Open"]
        color = "rgba(38,166,154,0.15)" if is_bull else "rgba(239,83,80,0.15)"
        border = "#26a69a" if is_bull else "#ef5350"
        label = "Bullish OB" if is_bull else "Bearish OB"
        # Extend OB zone to right edge
        x_end = idx[-1]
        body_top = max(row["Open"], row["Close"])
        body_bot = min(row["Open"], row["Close"])
        fig.add_shape(
            type="rect",
            x0=ts, x1=x_end,
            y0=body_bot, y1=body_top,
            fillcolor=color,
            line=dict(color=border, width=1),
            row=1, col=1,
        )
        fig.add_annotation(
            x=ts, y=body_top,
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
