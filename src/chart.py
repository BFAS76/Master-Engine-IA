import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def build_chart(
    df: pd.DataFrame,
    stats: dict,
    sl: float,
    tp1: float,
    tp2: float,
    tp3: float,
    direcao: str,
    ativo_label: str,
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
