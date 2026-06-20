import sys
sys.path.insert(0, '.')
from src.engine import InstitutionalEngine
from src.assets import ASSETS
from src.chart import build_chart
import yfinance as yf
import pandas as pd

ticker = ASSETS["💱 Forex"]["EUR/USD"]["yf"]
df = yf.download(ticker, period="60d", interval="15m", auto_adjust=True, progress=False)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

engine = InstitutionalEngine(df)
df2, s, idx_h, idx_l = engine.processar_tudo()

close = float(df2["Close"].iloc[-1])
r = float(df2["ATR"].iloc[-1]) * 1.5
direcao = "COMPRA" if s["prob_alta"] > 50 else "VENDA"
sl  = close - r if direcao == "COMPRA" else close + r
tp1 = close + r if direcao == "COMPRA" else close - r
tp2 = close + r*2 if direcao == "COMPRA" else close - r*2
tp3 = close + r*3 if direcao == "COMPRA" else close - r*3

fig = build_chart(df2, s, sl, tp1, tp2, tp3, direcao, "EUR/USD", idx_h, idx_l)
print("Traces:", len(fig.data))
print("Harmonic trace:", any("Harmónico" in (t.name or "") for t in fig.data))
print("SUCESSO")
