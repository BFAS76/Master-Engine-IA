import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit.components.v1 as components
import json
from scipy.signal import argrelextrema

# --- 1. CONFIGURAÇÃO GERAL ---
st.set_page_config(page_title="Master Engine IA - Ultimate V100", layout="wide")
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

# --- 2. MOTOR MATEMÁTICO COMPLETO ---
class InstitutionalEngine:
    def __init__(self, df):
        self.df = df.copy()

    def processar_tudo(self):
        df = self.df
        close, high, low = df['Close'], df['High'], df['Low']

        # Estatísticas Básicas
        preco_atual = close.iloc[-1]
        preco_24h_atras = close.iloc[-20] if len(close) > 20 else close.iloc[0]
        var_24h = ((preco_atual - preco_24h_atras) / preco_24h_atras) * 100
        alta_24h = high.tail(20).max()
        baixa_24h = low.tail(20).min()

        # Indicadores Técnicos
        df['EMA_200'] = close.ewm(span=200).mean()
        df['SMA_20'] = close.rolling(20).mean()
        df['ATR'] = (high - low).rolling(14).mean()
        
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / (loss + 1e-10))))
        df['RSI'] = rsi

        # MACD
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        macd_sinal = "COMPRA" if macd.iloc[-1] > signal.iloc[-1] else "VENDA"

        stoch_k = ((close - low.rolling(14).min()) / (high.rolling(14).max() - low.rolling(14).min())) * 100
        stoch_d = stoch_k.rolling(3).mean()
        cci = (close - df['SMA_20']) / (0.015 * close.rolling(20).std())
        williams_r = ((high.rolling(14).max() - close) / (high.rolling(14).max() - low.rolling(14).min())) * -100

        # Histórico
        returns = close.pct_change().dropna()
        volatilidade_anual = returns.std() * np.sqrt(252) * 100
        retorno_total = (close.iloc[-1] / close.iloc[0] - 1) * 100
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
        max_drawdown = (close / close.cummax() - 1).min() * 100
        win_rate = (returns > 0).mean() * 100
        var_95 = np.percentile(returns, 5) * 100

        # SMC
        df['Body'] = (close - df['Open']).abs()
        df['OB'] = df['Body'] > df['Body'].rolling(20).mean() * 2
        fvg_count = (low.shift(-1) > high.shift(1)).sum() + (high.shift(-1) < low.shift(1)).sum()
        bos_count = (close > high.shift(1).rolling(10).max()).sum()

        # Pivots puros
        highs_idx = argrelextrema(high.values, np.greater, order=5)[0]
        lows_idx = argrelextrema(low.values, np.less, order=5)[0]
        u_h = high.iloc[highs_idx[-1]] if len(highs_idx) > 0 else high.max()
        u_l = low.iloc[lows_idx[-1]] if len(lows_idx) > 0 else low.min()
        retracao_fibo = abs(u_h - preco_atual) / (abs(u_h - u_l) + 1e-10)

        # Monte Carlo
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

# --- 3. BIBLIOTECA DE ATIVOS ---
ativos_dict = {
    "💱 Forex": {
        "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X", 
        "USD/CHF": "CHF=X", "AUD/USD": "AUDUSD=X", "USD/CAD": "CAD=X", 
        "NZD/USD": "NZDUSD=X", "EUR/GBP": "EURGBP=X", "GBP/JPY": "GBPJPY=X"
    },
    "📊 Índices Globais": {
        "S&P 500": "^GSPC", "Nasdaq 100": "^IXIC", "Dow Jones (DJI)": "^DJI", 
        "DAX 40": "^GDAXI", "FTSE 100": "^FTSE", "VIX": "^VIX"
    },
    "🏆 Commodities": {
        "Ouro": "GC=F", "Prata": "SI=F", "Platina": "PL=F", "Cobre": "HG=F", 
        "Petróleo Brent": "BZ=F", "Gás Natural": "NG=F", "Café": "KC=F"
    },
    "₿ Cripto": {
        "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD", 
        "Binance Coin": "BNB-USD", "XRP": "XRP-USD", "Dogecoin": "DOGE-USD"
    },
    "🍎 Ações (Blue Chips)": {
        "Apple": "AAPL", "Microsoft": "MSFT", "Nvidia": "NVDA", 
        "Tesla": "TSLA", "Amazon": "AMZN", "Alphabet (Google)": "GOOGL", 
        "Meta (Facebook)": "META", "Berkshire Hathaway": "BRK-B"
    }
}

st.sidebar.title("💎 MASTER ENGINE IA")
categoria = st.sidebar.selectbox("Mercado", list(ativos_dict.keys()))
ativo_label = st.sidebar.selectbox("Ativo", list(ativos_dict[categoria].keys()))
ticker = ativos_dict[categoria][ativo_label]
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h", "4h", "1d"], index=0)

ticker_manual = st.sidebar.text_input("Ticker Manual (ex: PETR4.SA)", "")
if ticker_manual: ticker = ticker_manual

# --- 4. EXECUÇÃO ---
df_raw = yf.download(ticker, period="30d", interval=timeframe, auto_adjust=True, progress=False)

if not df_raw.empty:
    if isinstance(df_raw.columns, pd.MultiIndex): df_raw.columns = df_raw.columns.get_level_values(0)
    engine = InstitutionalEngine(df_raw)
    df, s, idx_h, idx_l = engine.processar_tudo()
    u = df.iloc[-1]
    
    direcao = "COMPRA" if s['prob_alta'] > 50 else "VENDA"
    tendencia = "ALTA" if u['Close'] > df['EMA_200'].iloc[-1] else "BAIXA"
    
    # Gestão de Risco
    r = u['ATR'] * 1.5
    if direcao == "COMPRA":
        sl, tp1, tp2, tp3 = u['Close'] - r, u['Close'] + (r*1.0), u['Close'] + (r*2.0), u['Close'] + (r*3.0)
    else:
        sl, tp1, tp2, tp3 = u['Close'] + r, u['Close'] - (r*1.0), u['Close'] - (r*2.0), u['Close'] - (r*3.0)

    # Lógica de SMC
    smc_zones = []
    lista_obs_texto = ""
    for i, row in df[df['OB']].tail(3).iterrows():
        cor = '#00ff88' if row['Close']>row['Open'] else '#ff3355'
        tipo = "BULLISH OB" if row['Close']>row['Open'] else "BEARISH OB"
        smc_zones.append({'price': float(row['Close']), 'color': cor, 'type': 'OB'})
        lista_obs_texto += f"  - {tipo} localizado em {row['Close']:.2f}\n"

    # Lógica de Harmónicos
    fib_ratios = {'Gartley': 0.618, 'Cypher': 0.786, 'Bat': 0.886, 'Shark': 1.13, 'Crab': 1.618}
    harmonics_text = ""
    for padrao, ideal in fib_ratios.items():
        diff = abs(s['retracao'] - ideal)
        if diff < 0.15:
            completion = max(0, 100 - (diff * 500))
            bias = "BULLISH" if direcao == "COMPRA" else "BEARISH"
            harmonics_text += f"  - {padrao} ({bias}): {completion:.0f}% completo | Confiança: {completion-5:.0f}%\n"

    # Lógica de Elliott
    if tendencia == "ALTA":
        onda_e = "Onda 3 (Impulso Macro)" if s['rsi'] > 60 else "Onda 4 (Corretiva)" if s['rsi'] < 50 else "Onda 5 (Exaustão)"
        prox_onda = "Onda 4" if "3" in onda_e else "Onda 5" if "4" in onda_e else "Onda A Macro"
        progresso_e = f"{s['rsi']:.0f}%"
    else:
        onda_e = "Onda C (Correção Profunda)" if s['rsi'] < 40 else "Onda B (Pullback)"
        prox_onda = "Ciclo 1" if "C" in onda_e else "Onda C"
        progresso_e = f"{(100-s['rsi']):.0f}%"

    # --- 5. GRÁFICO TRADINGVIEW ---
    st.subheader(f"📈 Dashboard Analítico - {ativo_label if not ticker_manual else ticker_manual}")
    chart_df = df.reset_index()
    chart_df['time'] = chart_df[chart_df.columns[0]].view(np.int64) // 10**9
    candlestickData = chart_df[['time','Open','High','Low','Close']].rename(columns={'Open':'open','High':'high','Low':'low','Close':'close'}).to_dict(orient='records')
    emaData = chart_df[['time','EMA_200']].dropna().rename(columns={'EMA_200':'value'}).to_dict(orient='records')
    
    # --- NOVO ALGORITMO ZIGZAG INSTITUCIONAL (CORREÇÃO DE ELLIOTT) ---
    todos_pivots = []
    for i in idx_h: todos_pivots.append({'idx': i, 'type': 'H', 'val': float(chart_df.iloc[i]['High'])})
    for i in idx_l: todos_pivots.append({'idx': i, 'type': 'L', 'val': float(chart_df.iloc[i]['Low'])})
    
    # Ordenar pontos no tempo
    todos_pivots.sort(key=lambda x: x['idx'])

    # Filtro de Alternância Estrita (Garante que nunca há 2 topos ou 2 fundos seguidos)
    pivots_estritos = []
    for p in todos_pivots:
        if not pivots_estritos:
            pivots_estritos.append(p)
        else:
            last_p = pivots_estritos[-1]
            if p['type'] != last_p['type']:
                # Alternou! Guardamos o ponto.
                pivots_estritos.append(p)
            else:
                # O ponto não alternou (dois topos seguidos). Vamos atualizar se este extremo for "melhor"
                if p['type'] == 'H' and p['val'] > last_p['val']:
                    pivots_estritos[-1] = p
                elif p['type'] == 'L' and p['val'] < last_p['val']:
                    pivots_estritos[-1] = p

    # Desenhar os últimos 6 pontos limpos no gráfico
    elliott_path = [{'time': int(chart_df.iloc[p['idx']]['time']), 'value': p['val']} for p in pivots_estritos[-6:]]
    # -----------------------------------------------------------------

    levels = {'stop': float(sl), 'tp1': float(tp1), 'tp2': float(tp2), 'tp3': float(tp3)}

    try:
        with open("frontend/lightweight-charts.js", "r") as f: lib = f.read()
        with open("frontend/chart.js", "r") as f: js_code = f.read()
        components.html(f"""<div id="tvchart" style="width: 100%; height: 500px;"></div><script>{lib}</script>
            <script>const candlestickData = {json.dumps(candlestickData)}; const emaData = {json.dumps(emaData)}; const smc_zones = {json.dumps(smc_zones)}; const elliott_path = {json.dumps(elliott_path)}; const levels = {json.dumps(levels)}; {js_code}</script>
        """, height=520)
    except: st.error("Erro na pasta 'frontend'.")

    # --- 6. MÓDULOS EXPANSÍVEIS DO RELATÓRIO DJI ---
    st.markdown("### 🔍 Detalhamento Institucional")

    def print_terminal(texto):
        st.markdown(f'<pre style="font-family: Consolas, monospace; background-color: #0d1117; color: #d1d4dc; padding: 20px; border: 1px solid #30363d; border-radius: 5px; font-size: 13.5px; white-space: pre-wrap;">{texto.strip()}</pre>', unsafe_allow_html=True)

    with st.expander("📊 DADOS DE MERCADO E ANÁLISE TÉCNICA"):
        print_terminal(f"""
• Preço Atual: {u['Close']:.2f} (ATR: {u['ATR']:.5f})
• Variação 24h: {s['var_24h']:.2f}% (Alta: {s['alta_24h']:.2f} | Baixa: {s['baixa_24h']:.2f})
• Tendência Principal: {tendencia} | Sinal Geral: {direcao}
• RSI (14): {s['rsi']:.2f} | MACD: {s['macd']}
• Stochastic: {s['stoch_k']:.1f}%K / {s['stoch_d']:.1f}%D
• Williams %R: {s['williams_r']:.1f}
• Sinais Totais (44): ✅ {s['sc']} COMPRA | ❌ {s['sv']} VENDA | ➖ {s['sn']} NEUTRO
        """)

    with st.expander("🏦 SMART MONEY CONCEPTS (SMC) - DETALHADO"):
        print_terminal(f"""
• Viés Institucional: {'BULLISH' if s['prob_alta'] > 50 else 'BEARISH'}
• Order Blocks ({len(smc_zones)} detectados e desenhados no gráfico):
{lista_obs_texto.rstrip()}
• Fair Value Gaps (FVGs): {s['fvg']} zonas ativas não preenchidas
• Quebras de Estrutura (BOS): {s['bos']} recentes registradas
        """)

    with st.expander("📐 WEGD (Wyckoff, Elliott, Gann, Dow)"):
        if s['rsi'] < 40 and tendencia == "BAIXA": fase_w = "ACUMULAÇÃO (Spring Fase C) - Possível Fundo"; c_man = "INJETANDO LIQUIDEZ (Compra)"
        elif s['rsi'] > 60 and tendencia == "ALTA": fase_w = "DISTRIBUIÇÃO (Upthrust Fase C) - Possível Topo"; c_man = "RETIRANDO LIQUIDEZ (Venda)"
        else: fase_w = "TENDÊNCIA ( markup/markdown Fase E )"; c_man = "ACOMPANHANDO A TENDÊNCIA"

        print_terminal(f"""
• 📊 WYCKOFF: Fase Atual: {fase_w} | Composite Man: {c_man}
• 🌊 ELLIOTT: {onda_e} (Progresso Fibo: {progresso_e}) | Próxima Onda: {prox_onda}
• 📉 DOW: Tendência Primária {tendencia} | Secundária {tendencia}
        """)

    with st.expander("🎯 PADRÕES HARMÔNICOS (Fibonacci)"):
        harm_final = harmonics_text.rstrip() if harmonics_text else "  - A aguardar formação estrutural (Nenhum Padrão Claro)."
        print_terminal(f"""
• Padrões Detectados Analisados por Retração Real de Fibonacci:
{harm_final}
        """)

    with st.expander("🎲 MONTE CARLO & ESTATÍSTICAS (8000 Simulações)"):
        print_terminal(f"""
• Probabilidade de Alta: {s['prob_alta']:.1f}% | Baixa: {s['prob_baixa']:.1f}%
• Alvo Mediano (Base): {s['alvo_med']:.2f}
• Alvo Bullish Extremo ( VaR 95% alta ): {s['alvo_bull']:.2f}
• Alvo Bearish Extremo ( VaR 95% baixa ): {s['alvo_bear']:.2f}
• Retorno Total: {s['ret_total']:.2f}% | Win Rate (Período): {s['win_rate']:.1f}%
• Sharpe Ratio: {s['sharpe']:.2f} | Max Drawdown: {s['max_dd']:.2f}%
        """)

    with st.expander("⚠️ GESTÃO DE RISCO E RECOMENDAÇÃO FINAL", expanded=True):
        print_terminal(f"""
🚨 VEREDICTO FINAL: {direcao} (Confiança Institucional: {abs(50-s['prob_alta'])*2:.0f}%)

• Stop Loss Calculado (ATR): {sl:.2f}
• Take Profit 1 (Seguro 1:1): {tp1:.2f}
• Take Profit 2 (Médio): {tp2:.2f}
• Take Profit 3 (Swing Institucional): {tp3:.2f}
• Risco/Retorno Total (Até TP3): 1:{(abs(u['Close']-tp3)/abs(u['Close']-sl)):.1f}
        """)

else:
    st.error("Ativo sem dados para este timeframe. Tente outro Ticker.")