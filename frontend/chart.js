function waitForLibrary(callback) {
    if (typeof LightweightCharts !== 'undefined') { callback(); } 
    else { setTimeout(function() { waitForLibrary(callback); }, 100); }
}

waitForLibrary(function() {
    const chartContainer = document.getElementById('tvchart');
    if (!chartContainer) return;

    // Criar a Barra de Ferramentas Flutuante
    const toolbar = document.createElement('div');
    toolbar.style.position = 'absolute';
    toolbar.style.top = '10px';
    toolbar.style.right = '10px';
    toolbar.style.zIndex = '1000';
    toolbar.style.display = 'flex';
    toolbar.style.gap = '8px';
    
    toolbar.innerHTML = `
        <button id="btn-camera" style="background:#161b22; color:#58a6ff; border:1px solid #30363d; padding:6px 12px; border-radius:4px; cursor:pointer; font-family:Consolas, monospace; transition: 0.2s;">📷 Print</button>
        <button id="btn-fullscreen" style="background:#161b22; color:#58a6ff; border:1px solid #30363d; padding:6px 12px; border-radius:4px; cursor:pointer; font-family:Consolas, monospace; transition: 0.2s;">⛶ Fullscreen</button>
    `;
    chartContainer.style.position = 'relative';
    chartContainer.appendChild(toolbar);

    const chart = LightweightCharts.createChart(chartContainer, {
        layout: { backgroundColor: '#0e1117', textColor: '#d1d4dc' },
        grid: { vertLines: { color: '#1f2937' }, horzLines: { color: '#1f2937' } },
        rightPriceScale: { borderColor: '#374151', visible: true },
        timeScale: { borderColor: '#374151', timeVisible: true },
    });

    const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#00ff88', downColor: '#ff3355', borderDownColor: '#ff3355',
        borderUpColor: '#00ff88', wickDownColor: '#ff3355', wickUpColor: '#00ff88',
    });
    
    if (typeof candlestickData !== 'undefined') candlestickSeries.setData(candlestickData);

    if (typeof emaData !== 'undefined' && emaData.length > 0) {
        const emaSeries = chart.addLineSeries({ color: '#f97316', lineWidth: 1, title: 'EMA 200' });
        emaSeries.setData(emaData);
    }

    if (typeof elliott_path !== 'undefined' && elliott_path.length > 0) {
        const elliottSeries = chart.addLineSeries({ color: '#58a6ff', lineWidth: 2, lineStyle: LightweightCharts.LineStyle.Dotted, title: 'Elliott Wave' });
        elliottSeries.setData(elliott_path);
    }

    if (typeof smc_zones !== 'undefined') {
        smc_zones.forEach(zone => {
            candlestickSeries.createPriceLine({
                price: zone.price, color: zone.color, lineWidth: 2, lineStyle: LightweightCharts.LineStyle.Solid, title: zone.type
            });
        });
    }

    if (typeof levels !== 'undefined') {
        candlestickSeries.createPriceLine({ price: levels.stop, color: '#ff4444', lineWidth: 2, lineStyle: LightweightCharts.LineStyle.Dashed, title: 'STOP LOSS' });
        candlestickSeries.createPriceLine({ price: levels.tp1, color: '#00ff88', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dashed, title: 'TP 1' });
        candlestickSeries.createPriceLine({ price: levels.tp2, color: '#00cc66', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dashed, title: 'TP 2' });
        candlestickSeries.createPriceLine({ price: levels.tp3, color: '#00994d', lineWidth: 2, lineStyle: LightweightCharts.LineStyle.Dashed, title: 'TP 3' });
    }

    chart.timeScale().fitContent();

    // Funções dos Botões
    document.getElementById('btn-fullscreen').addEventListener('click', () => {
        if (!document.fullscreenElement) { chartContainer.requestFullscreen(); } 
        else { document.exitFullscreen(); }
    });

    document.getElementById('btn-camera').addEventListener('click', () => {
        const canvas = chartContainer.querySelector('canvas');
        if(canvas) {
            const a = document.createElement('a');
            a.href = canvas.toDataURL('image/png');
            a.download = 'Master_Engine_Analise.png';
            a.click();
        }
    });
});