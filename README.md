# BFAS76 Charts — Master Engine IA

Dashboard de análise técnica institucional em tempo real, construído com Streamlit.

## Funcionalidades

- **44 sinais combinados**: RSI, MACD, EMA-200, Stochastic, CCI, Williams %R
- **Smart Money Concepts**: Order Blocks, Fair Value Gaps, Break of Structure
- **Padrões Harmónicos**: Gartley, Cypher, Bat, Shark, Crab
- **WEGD**: Wyckoff, Elliott, Gann, Dow
- **Monte Carlo** (8 000 simulações) — probabilidade direcional
- **Gestão de risco**: SL + TP1/TP2/TP3 dinâmicos via ATR
- **Gráfico TradingView** integrado com todos os timeframes
- **50+ ativos**: Forex, Índices, Commodities, Cripto, Blue Chips

## Instalação local

```bash
git clone https://github.com/BFAS76/Master-Engine-IA.git
cd Master-Engine-IA
pip install -r requirements.txt
streamlit run app.py
```

Abre em `http://localhost:8501`

## GitHub Codespaces

Clica em **Code → Codespaces → New codespace** — o ambiente arranca automaticamente.

## Estrutura

```
app.py              # Entrypoint UI (Streamlit)
src/
  engine.py         # Motor matemático (InstitutionalEngine)
  assets.py         # Dicionário de ativos por categoria
requirements.txt    # Dependências com versões fixas
packages.txt        # Pacotes sistema (apt) para devcontainer
.devcontainer/
  devcontainer.json # Config GitHub Codespaces
```

## Criado por BFAS76 ©
