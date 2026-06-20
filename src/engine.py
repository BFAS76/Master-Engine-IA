import numpy as np
import pandas as pd
from scipy.signal import argrelextrema


class InstitutionalEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def processar_tudo(self) -> tuple[pd.DataFrame, dict, np.ndarray, np.ndarray]:
        df = self.df
        close, high, low = df["Close"], df["High"], df["Low"]

        preco_atual = float(close.iloc[-1])
        preco_24h_atras = float(close.iloc[-20] if len(close) > 20 else close.iloc[0])
        var_24h = (preco_atual - preco_24h_atras) / preco_24h_atras * 100
        alta_24h = float(high.tail(20).max())
        baixa_24h = float(low.tail(20).min())

        df["EMA_200"] = close.ewm(span=200).mean()
        df["SMA_20"] = close.rolling(20).mean()
        df["ATR"] = (high - low).rolling(14).mean()

        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain / (loss + 1e-10)))
        df["RSI"] = rsi

        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        macd_sinal = "COMPRA" if macd.iloc[-1] > signal.iloc[-1] else "VENDA"

        stoch_k = (
            (close - low.rolling(14).min())
            / (high.rolling(14).max() - low.rolling(14).min())
        ) * 100
        stoch_d = stoch_k.rolling(3).mean()
        cci = (close - df["SMA_20"]) / (0.015 * close.rolling(20).std())
        williams_r = (
            (high.rolling(14).max() - close)
            / (high.rolling(14).max() - low.rolling(14).min())
        ) * -100

        returns = close.pct_change().dropna()
        vol_std = float(returns.std()) if len(returns) > 1 else 1e-10
        volatilidade_anual = vol_std * np.sqrt(252) * 100
        retorno_total = (float(close.iloc[-1]) / float(close.iloc[0]) - 1) * 100
        sharpe = (float(returns.mean()) / vol_std) * np.sqrt(252) if vol_std != 0 else 0
        max_drawdown = float((close / close.cummax() - 1).min()) * 100
        win_rate = float((returns > 0).mean()) * 100
        var_95 = float(np.percentile(returns, 5)) * 100

        df["Body"] = (close - df["Open"]).abs()
        df["OB"] = df["Body"] > df["Body"].rolling(20).mean() * 2
        fvg_count = int(
            (low.shift(-1) > high.shift(1)).sum() + (high.shift(-1) < low.shift(1)).sum()
        )
        bos_count = int((close > high.shift(1).rolling(10).max()).sum())

        highs_idx = argrelextrema(high.values, np.greater, order=5)[0]
        lows_idx = argrelextrema(low.values, np.less, order=5)[0]
        u_h = float(high.iloc[highs_idx[-1]]) if len(highs_idx) > 0 else float(high.max())
        u_l = float(low.iloc[lows_idx[-1]]) if len(lows_idx) > 0 else float(low.min())
        retracao_fibo = abs(u_h - preco_atual) / (abs(u_h - u_l) + 1e-10)

        # Monte Carlo — seed fixo para resultado determinístico por sessão
        rng = np.random.default_rng(seed=42)
        sims = preco_atual * np.exp(rng.normal(0, vol_std, 8_000))
        prob_alta = float((sims > preco_atual).mean()) * 100

        sinal_c = (
            int(float(rsi.iloc[-1]) / 10)
            + (4 if macd_sinal == "COMPRA" else 0)
            + (2 if preco_atual > float(df["EMA_200"].iloc[-1]) else 0)
        )
        sinal_v = (
            int((100 - float(rsi.iloc[-1])) / 10)
            + (4 if macd_sinal == "VENDA" else 0)
            + (2 if preco_atual < float(df["EMA_200"].iloc[-1]) else 0)
        )
        sinal_n = 44 - (sinal_c + sinal_v)

        stats = {
            "preco": preco_atual,
            "var_24h": var_24h,
            "alta_24h": alta_24h,
            "baixa_24h": baixa_24h,
            "rsi": float(rsi.iloc[-1]),
            "macd": macd_sinal,
            "stoch_k": float(stoch_k.iloc[-1]),
            "stoch_d": float(stoch_d.iloc[-1]),
            "cci": float(cci.iloc[-1]),
            "williams_r": float(williams_r.iloc[-1]),
            "atr": float(df["ATR"].iloc[-1]),
            "ret_total": retorno_total,
            "vol_anual": volatilidade_anual,
            "sharpe": sharpe,
            "max_dd": max_drawdown,
            "win_rate": win_rate,
            "var_95": var_95,
            "prob_alta": prob_alta,
            "prob_baixa": 100 - prob_alta,
            "alvo_bull": float(np.percentile(sims, 80)),
            "alvo_med": float(np.median(sims)),
            "alvo_bear": float(np.percentile(sims, 20)),
            "fvg": fvg_count,
            "bos": bos_count,
            "retracao": retracao_fibo,
            "sc": sinal_c,
            "sv": sinal_v,
            "sn": sinal_n,
        }

        return df, stats, highs_idx, lows_idx
