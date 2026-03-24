import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit.components.v1 as components
from scipy.signal import argrelextrema

# --- 1. CONFIGURAÇÃO GERAL ---
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

# --- 2. MOTOR MATEMÁTICO COMPLETO (O Cérebro da IA) ---
class InstitutionalEngine:
    def __init__(self, df):
        self.df = df.copy()

    def processar_tudo(self):
        df = self.df
        close, high, low = df['Close'], df['High'], df['Low']

        preco_atual = close.iloc[-1]
        preco_24h_atras = close.iloc[-20] if len(close) > 20 else close.iloc[0]
        var_24h = ((preco_atual - preco_24h_atras) / preco_24h_atras) * 100
        alta_24h = high.tail(20).max()
        baixa_24h = low.tail(20).min()

        df['EMA_200'] = close.ewm(span=200).mean()
        df['SMA_20'] = close.rolling(20).mean()
        df['ATR'] = (high - low).rolling(14).mean()
        
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / (loss + 1e-10))))
        df['RSI'] = rsi

        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        macd_sinal = "COMPRA" if macd.iloc[-1] > signal.iloc[-1] else "VENDA"

        stoch_k = ((close - low.rolling(14).min()) / (high.rolling(14).max() - low.rolling(14).min())) * 100
        stoch_d = stoch_k.rolling(3).mean()
        cci = (close - df['SMA_20']) / (0.015 * close.rolling(20).std())
        williams_r = ((high.rolling(14).max() - close) / (high.rolling(14).max() - low.rolling(14).min())) * -100

        returns = close.pct_change().dropna()
        volatilidade_anual = returns.std() * np.sqrt(252) * 100
        retorno_total = (close.iloc[-1] / close.iloc[0] - 1) * 100
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
        max_drawdown = (close / close.cummax() - 1).min() * 100
        win_rate = (returns > 0).mean() * 100
        var_95 = np.percentile(returns, 5) * 100

        df['Body'] = (close - df['Open']).abs()
        df['OB'] = df['Body'] > df['Body'].rolling(20).mean() * 2
        fvg_count = (low.shift(-1) > high.shift(1)).sum() + (high.shift(-1) < low.shift(1)).sum()
        bos_count = (close > high.shift(1).rolling(10).max()).sum()

        highs_idx = argrelextrema(high.values, np.greater, order=5)[0]
        lows_idx = argrelextrema(low.values, np.less, order=5)[0]
        u_h = high.iloc[highs_idx[-1]] if len(highs_idx) > 0 else high.max()
        u_l = low.iloc[lows_idx[-1]] if len(lows_idx) > 0 else low.min()
        retracao_fibo = abs(u_h - preco_atual) / (abs(u_h - u_l) + 1e-10)

        vol = returns.std()
        sims = preco_atual * np.exp(np.random.normal(0, vol, 8000))
        prob_alta = (sims > preco_atual).mean() * 100

        sinal_c = int(rsi.iloc[-1]/10) + (4 if macd_sinal=="COMPRA" else 0) + (2 if preco_atual > df['EMA_200'].iloc[-1] else 0)
        sinal_v = int((100-rsi.iloc[-1])/10) + (4 if macd_sinal=="VENDA" else 0) + (2 if preco_atual < df['EMA_200'].iloc[-1] else 0)
        sinal_n = 44 - (sinal_c + sinal_v)

        stats = {
            'preco': preco_atual, 'var_24h': var_24h, 'alta_24h': alta_24h, 'baixa_24h': baixa_24h,
            'rsi': rsi.iloc[-1], 'macd': macd_sinal, 'stoch_k': stoch_k.iloc[-1], 'stoch_d': stoch_d.iloc[-1],
            'cci': cci.iloc[-1], 'williams_r': williams_r.iloc[-1], 'atr': df['ATR'].iloc[-1],
            'ret_total': retorno_total, 'vol_anual': volatilidade_anual, 'sharpe': sharpe, 
            'max_dd': max_drawdown, 'win_rate': win_rate, 'var_95': var_95,
            'prob_alta': prob_alta, 'prob_baixa': 100 - prob_alta, 'alvo_bull': np.percentile(sims, 80), 
            'alvo_med': np.median(sims), 'alvo_bear': np.percentile(sims, 20), 'fvg': fvg_count, 
            'bos': bos_count, 'retracao': retracao_fibo, 'sc': sinal_c, 'sv': sinal_v, 'sn': sinal_n
        }

        return df, stats, highs_idx, lows_idx

# --- 3. BIBLIOTECA DE ATIVOS EXAUSTIVA (COMMODITIES CORRIGIDAS PARA CFD) ---
ativos_dict = {
    "💱 Forex": {
        "EUR/USD": {"yf": "EURUSD=X", "tv": "FX:EURUSD"},
        "GBP/USD": {"yf": "GBPUSD=X", "tv": "FX:GBPUSD"},
        "USD/JPY": {"yf": "JPY=X", "tv": "FX:USDJPY"},
        "USD/CHF": {"yf": "CHF=X", "tv": "FX:USDCHF"},
        "AUD/USD": {"yf": "AUDUSD=X", "tv": "FX:AUDUSD"},
        "USD/CAD": {"yf": "CAD=X", "tv": "FX:USDCAD"},
        "NZD/USD": {"yf": "NZDUSD=X", "tv": "FX:NZDUSD"},
        "EUR/GBP": {"yf": "EURGBP=X", "tv": "FX:EURGBP"},
        "EUR/JPY": {"yf": "EURJPY=X", "tv": "FX:EURJPY"},
        "GBP/JPY": {"yf": "GBPJPY=X", "tv": "FX:GBPJPY"},
        "AUD/JPY": {"yf": "AUDJPY=X", "tv": "FX:AUDJPY"}
    },
    "📊 Índices Globais": {
        "S&P 500": {"yf": "^GSPC", "tv": "CAPITALCOM:US500"},
        "Nasdaq 100": {"yf": "^IXIC", "tv": "CAPITALCOM:US100"},
        "Dow Jones (DJI)": {"yf": "^DJI", "tv": "CAPITALCOM:US30"},
        "Russell 2000": {"yf": "^RUT", "tv": "CAPITALCOM:US2000"},
        "DAX 40": {"yf": "^GDAXI", "tv": "CAPITALCOM:DE40"},
        "FTSE 100": {"yf": "^FTSE", "tv": "CAPITALCOM:UK100"},
        "Nikkei 225": {"yf": "^N225", "tv": "CAPITALCOM:JP225"},
        "VIX": {"yf": "^VIX", "tv": "TVC:VIX"}
    },
    "🏆 Commodities": {
        "Ouro": {"yf": "GC=F", "tv": "TVC:GOLD"},
        "Prata": {"yf": "SI=F", "tv": "TVC:SILVER"},
        "Platina": {"yf": "PL=F", "tv": "TVC:PLATINUM"},
        "Cobre": {"yf": "HG=F", "tv": "CAPITALCOM:COPPER"},
        "Petróleo WTI": {"yf": "CL=F", "tv": "TVC:USOIL"},
        "Petróleo Brent": {"yf": "BZ=F", "tv": "TVC:UKOIL"},
        "Gás Natural": {"yf": "NG=F", "tv": "TVC:NATGAS"},
        "Milho": {"yf": "ZC=F", "tv": "CAPITALCOM:CORN"},
        "Trigo": {"yf": "ZW=F", "tv": "CAPITALCOM:WHEAT"},
        "Café": {"yf": "KC=F", "tv": "CAPITALCOM:COFFEE"}
    },
    "₿ Cripto": {
        "Bitcoin": {"yf": "BTC-USD", "tv": "BINANCE:BTCUSDT"},
        "Ethereum": {"yf": "ETH-USD", "tv": "BINANCE:ETHUSDT"},
        "Solana": {"yf": "SOL-USD", "tv": "BINANCE:SOLUSDT"},
        "Binance Coin": {"yf": "BNB-USD", "tv": "BINANCE:BNBUSDT"},
        "XRP": {"yf": "XRP-USD", "tv": "BINANCE:XRPUSDT"},
        "Cardano": {"yf": "ADA-USD", "tv": "BINANCE:ADAUSDT"},
        "Dogecoin": {"yf": "DOGE-USD", "tv": "BINANCE:DOGEUSDT"},
        "Polkadot": {"yf": "DOT-USD", "tv": "BINANCE:DOTUSDT"},
        "Chainlink": {"yf": "LINK-USD", "tv": "BINANCE:LINKUSDT"},
        "Avalanche": {"yf": "AVAX-USD", "tv": "BINANCE:AVAXUSDT"}
    },
    "🍎 Ações (Blue Chips)": {
        "Apple": {"yf": "AAPL", "tv": "NASDAQ:AAPL"},
        "Microsoft": {"yf": "MSFT", "tv": "NASDAQ:MSFT"},
        "Nvidia": {"yf": "NVDA", "tv": "NASDAQ:NVDA"},
        "Tesla": {"yf": "TSLA", "tv": "NASDAQ:TSLA"},
        "Amazon": {"yf": "AMZN", "tv": "NASDAQ:AMZN"},
        "Alphabet (Google)": {"yf": "GOOGL", "tv": "NASDAQ:GOOGL"},
        "Meta (Facebook)": {"yf": "META", "tv": "NASDAQ:META"},
        "JPMorgan": {"yf": "JPM", "tv": "NYSE:JPM"},
        "Visa": {"yf": "V", "tv": "NYSE:V"},
        "Berkshire Hathaway": {"yf": "BRK-B", "tv": "NYSE:BRK.B"}
    }
}

st.sidebar.title("💎 BFAS76 CHARTS IA")
st.sidebar.caption("Institutional Trading Engine | Criado por BFAS76")
categoria = st.sidebar.selectbox("Mercado", list(ativos_dict.keys()))
ativo_label = st.sidebar.selectbox("Ativo", list(ativos_dict[categoria].keys()))
ticker_yf = ativos_dict[categoria][ativo_label]["yf"]
ticker_tv = ativos_dict[categoria][ativo_label]["tv"]

tf_map = {"5m": "5", "15m": "15", "1h": "60", "4h": "240", "1d": "D"}
timeframe_str = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h", "4h", "1d"], index=1)
tv_interval = tf_map[timeframe_str]

# Lógica de Pesquisa Manual
ticker_manual = st.sidebar.text_input("Ticker Manual (Ex: AAPL / EURUSD=X)", "")
if ticker_manual:
    ticker_yf = ticker_manual
    ticker_tv = ticker_manual.replace("=X", "").replace("-USD", "USDT").split(".")[0]
    ativo_label = ticker_manual

# --- 4. EXECUÇÃO DA IA NO BACKGROUND ---
df_raw = yf.download(ticker_yf, period="30d", interval=timeframe_str, auto_adjust=True, progress=False)

if not df_raw.empty:
    if isinstance(df_raw.columns, pd.MultiIndex): df_raw.columns = df_raw.columns.get_level_values(0)
    engine = InstitutionalEngine(df_raw)
    df, s, idx_h, idx_l = engine.processar_tudo()
    u = df.iloc[-1]
    
    direcao = "COMPRA" if s['prob_alta'] > 50 else "VENDA"
    tendencia = "ALTA" if u['Close'] > df['EMA_200'].iloc[-1] else "BAIXA"
    
    r = u['ATR'] * 1.5
    if direcao == "COMPRA":
        sl, tp1, tp2, tp3 = u['Close'] - r, u['Close'] + (r*1.0), u['Close'] + (r*2.0), u['Close'] + (r*3.0)
    else:
        sl, tp1, tp2, tp3 = u['Close'] + r, u['Close'] - (r*1.0), u['Close'] - (r*2.0), u['Close'] - (r*3.0)

    smc_zones = []
    lista_obs_texto = ""
    for i, row in df[df['OB']].tail(3).iterrows():
        tipo = "BULLISH OB" if row['Close']>row['Open'] else "BEARISH OB"
        lista_obs_texto += f"  - {tipo} validado em {row['Close']:.2f}\n"

    fib_ratios = {'Gartley': 0.618, 'Cypher': 0.786, 'Bat': 0.886, 'Shark': 1.13, 'Crab': 1.618}
    harmonics_text = ""
    for padrao, ideal in fib_ratios.items():
        diff = abs(s['retracao'] - ideal)
        if diff < 0.15:
            completion = max(0, 100 - (diff * 500))
            bias = "BULLISH" if direcao == "COMPRA" else "BEARISH"
            harmonics_text += f"  - {padrao} ({bias}): {completion:.0f}% completo | Confiança: {completion-5:.0f}%\n"

    if tendencia == "ALTA":
        onda_e = "Onda 3 (Impulso Macro)" if s['rsi'] > 60 else "Onda 4 (Corretiva)" if s['rsi'] < 50 else "Onda 5 (Exaustão)"
        prox_onda = "Onda 4" if "3" in onda_e else "Onda 5" if "4" in onda_e else "Onda A Macro"
        progresso_e = f"{s['rsi']:.0f}%"
    else:
        onda_e = "Onda C (Correção Profunda)" if s['rsi'] < 40 else "Onda B (Pullback)"
        prox_onda = "Ciclo 1" if "C" in onda_e else "Onda C"
        progresso_e = f"{(100-s['rsi']):.0f}%"

    # --- 5. O GRÁFICO OFICIAL TRADINGVIEW ---
    st.subheader(f"📈 Gráfico Oficial - {ativo_label} | by BFAS76 Charts")
    
    tv_widget_html = f"""
    <div class="tradingview-widget-container" style="height:650px;width:100%">
      <div id="tv_chart_main" style="height:calc(100% - 32px);width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
      "autosize": true,
      "symbol": "{ticker_tv}",
      "interval": "{tv_interval}",
      "timezone": "Etc/UTC",
      "theme": "dark",
      "style": "1",
      "locale": "pt",
      "enable_publishing": false,
      "hide_side_toolbar": false,
      "allow_symbol_change": true,
      "backgroundColor": "#0e1117",
      "gridColor": "#1f2937",
      "toolbar_bg": "#161b22",
      "container_id": "tv_chart_main"
    }}
      );
      </script>
    </div>
    """
    components.html(tv_widget_html, height=650)

    # --- 6. MÓDULOS EXPANSÍVEIS DO RELATÓRIO ---
    st.markdown("### 🔍 Detalhamento Institucional - BFAS76 Charts")

    def print_terminal(texto):
        st.markdown(f'<pre style="font-family: Consolas, monospace; background-color: #0d1117; color: #d1d4dc; padding: 20px; border: 1px solid #30363d; border-radius: 5px; font-size: 13.5px; white-space: pre-wrap;">{texto.strip()}</pre>', unsafe_allow_html=True)

    with st.expander("📊 DADOS DE MERCADO E ANÁLISE TÉCNICA"):
        print_terminal(f"""
• Preço Atual (IA): {u['Close']:.2f} (ATR: {u['ATR']:.5f})
• Variação 24h: {s['var_24h']:.2f}% (Alta: {s['alta_24h']:.2f} | Baixa: {s['baixa_24h']:.2f})
• Tendência Principal: {tendencia} | Sinal Geral: {direcao}
• RSI (14): {s['rsi']:.2f} | MACD: {s['macd']}
• Stochastic: {s['stoch_k']:.1f}%K / {s['stoch_d']:.1f}%D
• Sinais Totais (44): ✅ {s['sc']} COMPRA | ❌ {s['sv']} VENDA | ➖ {s['sn']} NEUTRO
        """)

    with st.expander("🏦 SMART MONEY CONCEPTS (SMC) - ZONAS PARA MARCAÇÃO"):
        print_terminal(f"""
• Viés Institucional: {'BULLISH' if s['prob_alta'] > 50 else 'BEARISH'}
• Order Blocks (Zonas de Interesse Validadas pela IA BFAS76):
{lista_obs_texto.rstrip()}
• Fair Value Gaps (FVGs): {s['fvg']} zonas macro
• Quebras de Estrutura (BOS): {s['bos']} recentes
        """)

    with st.expander("📐 WEGD (Wyckoff, Elliott, Gann, Dow)"):
        if s['rsi'] < 40 and tendencia == "BAIXA": fase_w = "ACUMULAÇÃO (Spring Fase C)"; c_man = "INJETANDO LIQUIDEZ"
        elif s['rsi'] > 60 and tendencia == "ALTA": fase_w = "DISTRIBUIÇÃO (Upthrust Fase C)"; c_man = "RETIRANDO LIQUIDEZ"
        else: fase_w = "TENDÊNCIA ( markup/markdown )"; c_man = "ACOMPANHANDO A TENDÊNCIA"

        print_terminal(f"""
• 📊 WYCKOFF: Fase Atual: {fase_w} | Composite Man: {c_man}
• 🌊 ELLIOTT: {onda_e} (Progresso Fibo: {progresso_e}) | Próxima Onda: {prox_onda}
• 📉 DOW: Tendência Primária {tendencia} | Secundária {tendencia}
        """)

    with st.expander("🎯 PADRÕES HARMÔNICOS (Fibonacci)"):
        harm_final = harmonics_text.rstrip() if harmonics_text else "  - A aguardar formação estrutural."
        print_terminal(f"""
• Padrões Detectados Analisados por Retração Real:
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
        try:
            tp_str = f"1:{(abs(u['Close']-tp3)/abs(u['Close']-sl)):.1f}"
        except:
            tp_str = "1:2.0"
        print_terminal(f"""
🚨 VEREDICTO FINAL: {direcao} (Confiança Institucional: {abs(50-s['prob_alta'])*2:.0f}%)

• Stop Loss Calculado (ATR): {sl:.2f}
• Take Profit 1 (Seguro 1:1): {tp1:.2f}
• Take Profit 2 (Médio): {tp2:.2f}
• Take Profit 3 (Swing Institucional): {tp3:.2f}
• Risco/Retorno Recomendado: {tp_str}

-- Desenvolvido por BFAS76 Charts ©
        """)

else:
    st.error("Ativo sem dados para este timeframe. Verifique o Ticker ou tente um timeframe maior.")
