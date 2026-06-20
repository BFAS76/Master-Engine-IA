import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import yfinance as yf

from src.engine import InstitutionalEngine
from src.assets import ASSETS
from src.chart import build_chart

st.set_page_config(page_title="BFAS76 Charts - Master Engine IA", layout="wide")
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .streamlit-expanderHeader {
        background-color: #161b22;
        color: #58a6ff;
        font-weight: bold;
        border-radius: 5px;
        font-family: Consolas, monospace;
    }
</style>
""", unsafe_allow_html=True)


_PERIODO = {"5m": "5d", "15m": "60d", "1h": "730d", "4h": "730d", "1d": "5y"}

@st.cache_data(ttl=3600, show_spinner="A carregar dados de mercado...")
def carregar_dados(ticker: str, intervalo: str) -> pd.DataFrame:
    periodo = _PERIODO.get(intervalo, "60d")
    df = yf.download(ticker, period=periodo, interval=intervalo, auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def print_terminal(texto: str) -> None:
    st.markdown(
        f'<pre style="font-family:Consolas,monospace;background-color:#0d1117;'
        f'color:#d1d4dc;padding:20px;border:1px solid #30363d;border-radius:5px;'
        f'font-size:13.5px;white-space:pre-wrap;">{texto.strip()}</pre>',
        unsafe_allow_html=True,
    )


# --- SIDEBAR ---
st.sidebar.title("💎 BFAS76 CHARTS IA")
st.sidebar.caption("Institutional Trading Engine | Criado por BFAS76")

categoria = st.sidebar.selectbox("Mercado", list(ASSETS.keys()))
ativo_label = st.sidebar.selectbox("Ativo", list(ASSETS[categoria].keys()))
ticker_yf = ASSETS[categoria][ativo_label]["yf"]
ticker_tv = ASSETS[categoria][ativo_label]["tv"]

tf_map = {"5m": "5", "15m": "15", "1h": "60", "4h": "240", "1d": "D"}
timeframe_str = st.sidebar.selectbox("Timeframe", list(tf_map.keys()), index=1)
tv_interval = tf_map[timeframe_str]

ticker_manual = st.sidebar.text_input("Ticker Manual (Ex: AAPL / EURUSD=X)", "")
if ticker_manual:
    ticker_yf = ticker_manual
    ticker_tv = ticker_manual.replace("=X", "").replace("-USD", "USDT").split(".")[0]
    ativo_label = ticker_manual

# --- DADOS + MOTOR ---
df_raw = carregar_dados(ticker_yf, timeframe_str)

if df_raw.empty:
    st.error("Ativo sem dados para este timeframe. Verifique o Ticker ou tente um timeframe maior.")
    st.stop()

engine = InstitutionalEngine(df_raw)
df, s, idx_h, idx_l = engine.processar_tudo()
u = df.iloc[-1]

direcao = "COMPRA" if s["prob_alta"] > 50 else "VENDA"
tendencia = "ALTA" if u["Close"] > df["EMA_200"].iloc[-1] else "BAIXA"

r = u["ATR"] * 1.5
if direcao == "COMPRA":
    sl  = u["Close"] - r
    tp1 = u["Close"] + r
    tp2 = u["Close"] + r * 2
    tp3 = u["Close"] + r * 3
else:
    sl  = u["Close"] + r
    tp1 = u["Close"] - r
    tp2 = u["Close"] - r * 2
    tp3 = u["Close"] - r * 3

# Order Blocks
lista_obs_texto = ""
for _, row in df[df["OB"]].tail(3).iterrows():
    tipo = "BULLISH OB" if row["Close"] > row["Open"] else "BEARISH OB"
    lista_obs_texto += f"  - {tipo} validado em {row['Close']:.2f}\n"

# Harmónicos
fib_ratios = {"Gartley": 0.618, "Cypher": 0.786, "Bat": 0.886, "Shark": 1.13, "Crab": 1.618}
harmonics_text = ""
for padrao, ideal in fib_ratios.items():
    diff = abs(s["retracao"] - ideal)
    if diff < 0.15:
        completion = max(0, 100 - diff * 500)
        bias = "BULLISH" if direcao == "COMPRA" else "BEARISH"
        harmonics_text += f"  - {padrao} ({bias}): {completion:.0f}% completo | Confiança: {completion-5:.0f}%\n"

# Elliott
if tendencia == "ALTA":
    onda_e   = "Onda 3 (Impulso Macro)" if s["rsi"] > 60 else "Onda 4 (Corretiva)" if s["rsi"] < 50 else "Onda 5 (Exaustão)"
    prox_onda = "Onda 4" if "3" in onda_e else "Onda 5" if "4" in onda_e else "Onda A Macro"
    progresso_e = f"{s['rsi']:.0f}%"
else:
    onda_e   = "Onda C (Correção Profunda)" if s["rsi"] < 40 else "Onda B (Pullback)"
    prox_onda = "Ciclo 1" if "C" in onda_e else "Onda C"
    progresso_e = f"{100 - s['rsi']:.0f}%"

# Wyckoff
if s["rsi"] < 40 and tendencia == "BAIXA":
    fase_w, c_man = "ACUMULAÇÃO (Spring Fase C)", "INJETANDO LIQUIDEZ"
elif s["rsi"] > 60 and tendencia == "ALTA":
    fase_w, c_man = "DISTRIBUIÇÃO (Upthrust Fase C)", "RETIRANDO LIQUIDEZ"
else:
    fase_w, c_man = "TENDÊNCIA (markup/markdown)", "ACOMPANHANDO A TENDÊNCIA"

# --- GRÁFICO TRADINGVIEW ---
st.subheader(f"📈 Gráfico Oficial - {ativo_label} | by BFAS76 Charts")
components.html(f"""
<div class="tradingview-widget-container" style="height:650px;width:100%">
  <div id="tv_chart_main" style="height:calc(100% - 32px);width:100%"></div>
  <script src="https://s3.tradingview.com/tv.js"></script>
  <script>
  new TradingView.widget({{
    "autosize": true, "symbol": "{ticker_tv}", "interval": "{tv_interval}",
    "timezone": "Etc/UTC", "theme": "dark", "style": "1", "locale": "pt",
    "enable_publishing": false, "hide_side_toolbar": false,
    "allow_symbol_change": true, "backgroundColor": "#0e1117",
    "gridColor": "#1f2937", "toolbar_bg": "#161b22",
    "container_id": "tv_chart_main"
  }});
  </script>
</div>
""", height=650)

# --- GRÁFICO DE ANÁLISE PLOTLY ---
st.markdown("### 📊 Gráfico de Análise - BFAS76 Engine")
fig = build_chart(df, s, sl, tp1, tp2, tp3, direcao, ativo_label)
st.plotly_chart(fig, use_container_width=True)

# --- MÓDULOS RELATÓRIO ---
st.markdown("### 🔍 Detalhamento Institucional - BFAS76 Charts")

with st.expander("📊 DADOS DE MERCADO E ANÁLISE TÉCNICA"):
    print_terminal(f"""
• Preço Atual (IA): {u['Close']:.2f} (ATR: {u['ATR']:.5f})
• Variação 24h: {s['var_24h']:.2f}% (Alta: {s['alta_24h']:.2f} | Baixa: {s['baixa_24h']:.2f})
• Tendência Principal: {tendencia} | Sinal Geral: {direcao}
• RSI (14): {s['rsi']:.2f} | MACD: {s['macd']}
• Stochastic: {s['stoch_k']:.1f}%K / {s['stoch_d']:.1f}%D
• Sinais Totais (44): ✅ {s['sc']} COMPRA | ❌ {s['sv']} VENDA | ➖ {s['sn']} NEUTRO
    """)

with st.expander("🏦 SMART MONEY CONCEPTS (SMC)"):
    print_terminal(f"""
• Viés Institucional: {'BULLISH' if s['prob_alta'] > 50 else 'BEARISH'}
• Order Blocks (Zonas validadas):
{lista_obs_texto.rstrip()}
• Fair Value Gaps (FVGs): {s['fvg']} zonas macro
• Quebras de Estrutura (BOS): {s['bos']} recentes
    """)

with st.expander("📐 WEGD (Wyckoff, Elliott, Gann, Dow)"):
    print_terminal(f"""
• 📊 WYCKOFF: Fase: {fase_w} | Composite Man: {c_man}
• 🌊 ELLIOTT: {onda_e} (Progresso Fibo: {progresso_e}) | Próxima Onda: {prox_onda}
• 📉 DOW: Tendência Primária {tendencia} | Secundária {tendencia}
    """)

with st.expander("🎯 PADRÕES HARMÓNICOS (Fibonacci)"):
    harm_final = harmonics_text.rstrip() or "  - A aguardar formação estrutural."
    print_terminal(f"""
• Padrões detectados por retração real:
{harm_final}
    """)

with st.expander("🎲 MONTE CARLO & ESTATÍSTICAS (8000 Simulações)"):
    print_terminal(f"""
• Probabilidade de Alta: {s['prob_alta']:.1f}% | Baixa: {s['prob_baixa']:.1f}%
• Alvo Mediano: {s['alvo_med']:.2f}
• Alvo Bullish Extremo: {s['alvo_bull']:.2f} | Alvo Bearish: {s['alvo_bear']:.2f}
• Sharpe Ratio: {s['sharpe']:.2f} | Max Drawdown: {s['max_dd']:.2f}%
    """)

with st.expander("⚠️ GESTÃO DE RISCO E RECOMENDAÇÃO FINAL", expanded=True):
    rr_ratio = abs(u["Close"] - tp3) / max(abs(u["Close"] - sl), 1e-10)
    print_terminal(f"""
🚨 VEREDICTO FINAL: {direcao} (Confiança Institucional: {abs(50 - s['prob_alta']) * 2:.0f}%)

• Stop Loss Calculado (ATR): {sl:.2f}
• Take Profit 1 (Seguro 1:1): {tp1:.2f}
• Take Profit 2 (Médio):      {tp2:.2f}
• Take Profit 3 (Swing):      {tp3:.2f}
• Risco/Retorno Recomendado:  1:{rr_ratio:.1f}

-- Desenvolvido por BFAS76 Charts ©
    """)
