import sys; sys.path.insert(0, '.')
from src.engine import InstitutionalEngine
import yfinance as yf, pandas as pd

df = yf.download('ETH-USD', period='5d', interval='15m', auto_adjust=True, progress=False)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

engine = InstitutionalEngine(df)
df2, s, _, _ = engine.processar_tudo()

bull = int(df2["BullishOB"].sum())
bear = int(df2["BearishOB"].sum())
print(f"Bullish OBs detectados: {bull}")
print(f"Bearish OBs detectados: {bear}")

if bull > 0:
    row = df2[df2["BullishOB"]].iloc[-1]
    is_bearish_candle = row["Close"] < row["Open"]
    print(f"Bullish OB - vela bearish (correto=True): {is_bearish_candle}")

if bear > 0:
    row = df2[df2["BearishOB"]].iloc[-1]
    is_bullish_candle = row["Close"] > row["Open"]
    print(f"Bearish OB - vela bullish (correto=True): {is_bullish_candle}")
