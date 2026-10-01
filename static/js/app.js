// static/js/app.js

document.addEventListener("DOMContentLoaded", () => {
    // 0. Initialize Icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // 1. Navigation Logic (SPA)
    const navItems = document.querySelectorAll('.nav-item');
    const viewSections = document.querySelectorAll('.view-section');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            // Remove active from all navs & views
            navItems.forEach(nav => nav.classList.remove('active'));
            viewSections.forEach(view => view.classList.remove('active'));

            // Add active to clicked nav & corresponding view
            item.classList.add('active');
            const targetId = item.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');

            // Resize charts if dashboard is selected
            if (targetId === 'view-dashboard') {
                setTimeout(() => {
                    Plotly.Plots.resize('tvchart');
                    Plotly.Plots.resize('equitychart');
                }, 100);
            }
        });
    });

    // 2. Setup Plotly Chart
    const chartContainer = document.getElementById('tvchart');
    const equityContainer = document.getElementById('equitychart');
    
    let chartData = {
        x: [], open: [], high: [], low: [], close: [],
        type: 'candlestick', xaxis: 'x', yaxis: 'y', name: 'BTC/USDT',
        increasing: {line: {color: '#00E676'}}, // Updated Win Color
        decreasing: {line: {color: '#FF1744'}}  // Updated Loss Color
    };

    let equityData = {
        x: [], y: [],
        type: 'scatter', mode: 'lines', name: 'Équité ($)',
        line: {color: '#00E6F2', width: 3}, // Updated Accent Color
        fill: 'tozeroy', fillcolor: 'rgba(0, 230, 242, 0.1)'
    };

    const layout = {
        dragmode: 'zoom', margin: { r: 60, t: 30, b: 40, l: 60 }, showlegend: false,
        xaxis: { autorange: true, title: 'Time', type: 'category', gridcolor: 'rgba(255,255,255,0.05)', tickfont: { color: '#8A94A6' }, rangeslider: { visible: false } },
        yaxis: { autorange: true, gridcolor: 'rgba(255,255,255,0.05)', tickfont: { color: '#8A94A6' } },
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent'
    };

    const equityLayout = {
        margin: { r: 60, t: 30, b: 40, l: 60 }, showlegend: false,
        xaxis: { title: 'Time', type: 'category', gridcolor: 'rgba(255,255,255,0.05)', tickfont: { color: '#8A94A6' } },
        yaxis: { title: 'Équité ($)', gridcolor: 'rgba(255,255,255,0.05)', tickfont: { color: '#8A94A6' } },
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent'
    };

    Plotly.newPlot(chartContainer, [chartData], layout, {responsive: true});
    Plotly.newPlot(equityContainer, [equityData], equityLayout, {responsive: true});

    // 3. Setup WebSocket Logic
    const ws = new WebSocket(`ws://${location.host}/ws`);
    
    // UI Elements
    const btnStart = document.getElementById("btn-start");
    const btnStop = document.getElementById("btn-stop");
    const statusDot = document.getElementById("status-dot");
    const statusText = document.getElementById("status-text");
    const currentPriceEl = document.getElementById("current-price");
    const btnStrategy = document.getElementById("strategy-select");
    const badgeStrategy = document.getElementById("strategy-badge");
    
    // Portfolio Elements
    const valCash = document.getElementById("val-cash");
    const valEquity = document.getElementById("val-equity");
    const valWinrate = document.getElementById("val-winrate");
    const valProfitFactor = document.getElementById("val-profitfactor");
    const tbodyPositions = document.getElementById("positions-tbody");

    let lastPrice = 0;

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);

        if (msg.type === "init") {
            chartData.x = msg.candles.map(c => c.timestamp);
            chartData.open = msg.candles.map(c => c.open);
            chartData.high = msg.candles.map(c => c.high);
            chartData.low = msg.candles.map(c => c.low);
            chartData.close = msg.candles.map(c => c.close);
            
            equityData.x = msg.candles.map(c => c.timestamp);
            equityData.y = msg.candles.map(() => msg.portfolio.equity);
            
            Plotly.react(chartContainer, [chartData], layout);
            Plotly.react(equityContainer, [equityData], equityLayout);
            
            if(msg.candles.length > 0) {
                 lastPrice = msg.candles[msg.candles.length-1].close;
                 updatePriceDisplay(lastPrice);
            }
            updatePortfolio(msg.portfolio);
        }
        else if (msg.type === "update") {
            const c = msg.candle;
            
            const update = {
                x: [[c.timestamp]], open: [[c.open]], high: [[c.high]], low: [[c.low]], close: [[c.close]]
            };
            
            const eqUpdate = {
                x: [[c.timestamp]], y: [[msg.portfolio.equity]]
            };

            Plotly.extendTraces(chartContainer, update, [0]);
            Plotly.extendTraces(equityContainer, eqUpdate, [0]);
            
            const newPrice = c.close;
            updatePriceDisplay(newPrice, lastPrice);
            lastPrice = newPrice;
            
            updatePortfolio(msg.portfolio);
        }
        else if (msg.type === "backtest_result") {
            const resDiv = document.getElementById("backtest-results");
            if(resDiv) {
                resDiv.innerHTML = `
                    <div style="font-size: 1.1rem; margin-bottom: 12px;">
                        <strong>Total Trades :</strong> ${msg.stats.total_trades || 0}
                    </div>
                    <div style="font-size: 1.1rem; margin-bottom: 12px;">
                        <strong>Win Rate :</strong> <span style="color:var(--win-color)">${msg.stats["win_rate_%"] || 0}%</span>
                    </div>
                    <div style="font-size: 1.1rem;">
                        <strong>Profit/Pertes :</strong> <span class="pnl-pill ${(msg.stats.total_pnl >= 0) ? 'positive' : 'negative'}">${(msg.stats.total_pnl >= 0 ? '+' : '')}$${(msg.stats.total_pnl || 0).toFixed(2)}</span>
                    </div>
                `;
            }
        }
    };

    function updatePriceDisplay(newPrice, oldPrice) {
        currentPriceEl.innerText = `$${newPrice.toFixed(2)}`;
        if (oldPrice) {
            currentPriceEl.className = "current-price";
            if (newPrice > oldPrice) {
                currentPriceEl.classList.add("up");
            } else if (newPrice < oldPrice) {
                currentPriceEl.classList.add("down");
            }
        }
    }

    function updatePortfolio(portfolio) {
        valCash.innerText = `$${portfolio.cash.toFixed(2)}`;
        valEquity.innerText = `$${portfolio.equity.toFixed(2)}`;
        
        if (portfolio.stats && portfolio.stats["win_rate_%"] !== undefined) {
            valWinrate.innerText = `${portfolio.stats["win_rate_%"].toFixed(1)}%`;
            const pf = portfolio.stats["profit_factor"];
            valProfitFactor.innerText = (pf === "inf" || parseFloat(pf) > 9999) ? "∞" : parseFloat(pf).toFixed(2);
        }

        if (portfolio.positions && portfolio.positions.length > 0) {
            tbodyPositions.innerHTML = "";
            portfolio.positions.forEach(pos => {
                const tr = document.createElement("tr");
                const sidePillClass = pos.side === "long" ? "positive" : "negative";
                const sideIcon = pos.side === "long" ? "trending-up" : "trending-down";
                const pnlPillClass = pos.pnl >= 0 ? "positive" : "negative";
                const pnlSign = pos.pnl >= 0 ? '+' : '';
                
                tr.innerHTML = `
                    <td><div class="table-symbol"><i data-lucide="coins"></i> ${pos.symbol}</div></td>
                    <td><span class="pnl-pill ${sidePillClass}"><i data-lucide="${sideIcon}"></i> ${pos.side.toUpperCase()}</span></td>
                    <td>${pos.qty.toFixed(6)}</td>
                    <td>$${pos.entry.toFixed(2)}</td>
                    <td>$${pos.stop.toFixed(2)}</td>
                    <td>$${pos.tp.toFixed(2)}</td>
                    <td><span class="pnl-pill ${pnlPillClass}">${pnlSign}$${pos.pnl.toFixed(2)}</span></td>
                    <td><button class="btn btn-small outline secondary" onclick="closePosition('${pos.symbol}')"><i data-lucide="x"></i> Fermer</button></td>
                `;
                tbodyPositions.appendChild(tr);
            });
            if (typeof lucide !== 'undefined') lucide.createIcons();
        } else {
            tbodyPositions.innerHTML = `<tr><td colspan="8" class="empty-state"><i data-lucide="inbox"></i><p>Aucune position active pour le moment.</p></td></tr>`;
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }

        // Render History
        const tbodyHistory = document.getElementById("history-tbody");
        if (tbodyHistory) {
            if (portfolio.closed_trades && portfolio.closed_trades.length > 0) {
                tbodyHistory.innerHTML = "";
                portfolio.closed_trades.slice().reverse().forEach(trade => {
                    const tr = document.createElement("tr");
                    const pnlPillClass = trade.pnl >= 0 ? "positive" : "negative";
                    const pnlSign = trade.pnl >= 0 ? '+' : '';
                    
                    const dateObj = new Date(trade.timestamp);
                    const timeStr = dateObj.toLocaleTimeString();
                    
                    tr.innerHTML = `
                        <td>${timeStr}</td>
                        <td><div class="table-symbol">${trade.symbol}</div></td>
                        <td><span class="pnl-pill ${trade.side === 'long' ? 'positive' : 'negative'}">${trade.side.toUpperCase()}</span></td>
                        <td>$${trade.entry.toFixed(2)}</td>
                        <td>$${trade.exit.toFixed(2)}</td>
                        <td>${trade.reason}</td>
                        <td><span class="pnl-pill ${pnlPillClass}">${pnlSign}$${trade.pnl.toFixed(2)}</span></td>
                    `;
                    tbodyHistory.appendChild(tr);
                });
                if (typeof lucide !== 'undefined') lucide.createIcons();
            } else {
                tbodyHistory.innerHTML = `<tr><td colspan="7" class="empty-state"><i data-lucide="files"></i><p>Aucun historique disponible. Le bot n'a pas encore fermé de positions.</p></td></tr>`;
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
        }
    }

    // 4. Controls
    btnStart.addEventListener("click", () => {
        ws.send(JSON.stringify({ command: "start" }));
        statusDot.classList.add("active");
        statusText.innerText = "En cours d'exécution";
    });

    btnStop.addEventListener("click", () => {
        ws.send(JSON.stringify({ command: "stop" }));
        statusDot.classList.remove("active");
        statusText.innerText = "Arrêté";
    });
    
    btnStrategy.addEventListener("change", (e) => {
        const val = e.target.value;
        const text = e.target.options[e.target.selectedIndex].text;
        ws.send(JSON.stringify({ command: "set_strategy", value: val }));
        badgeStrategy.innerText = `Stratégie: ${text}`;
    });

    // 5. Manual Trading
    const btnBuy = document.querySelector('.action-buy');
    if (btnBuy) {
        btnBuy.addEventListener('click', () => {
            ws.send(JSON.stringify({ command: "manual_trade", side: "long" }));
        });
    }

    const btnSell = document.querySelector('.action-sell');
    if (btnSell) {
        btnSell.addEventListener('click', () => {
            ws.send(JSON.stringify({ command: "manual_trade", side: "short" }));
        });
    }

    // Expose closePosition function globally for the onclick handler
    window.closePosition = function(symbol) {
        ws.send(JSON.stringify({ command: "close_position", symbol: symbol }));
    };

    // 6. Settings
    const btnSaveSettings = document.getElementById("btn-save-settings");
    if(btnSaveSettings) {
        btnSaveSettings.addEventListener("click", () => {
            const leverage = document.getElementById("setting-leverage").value;
            const risk = document.getElementById("setting-risk").value;
            const apiKey = document.getElementById("setting-api-key").value;
            const apiSecret = document.getElementById("setting-api-secret").value;
            const discordUrl = document.getElementById("setting-discord").value;

            ws.send(JSON.stringify({
                command: "update_settings",
                leverage: parseFloat(leverage),
                risk: parseFloat(risk),
                api_key: apiKey,
                api_secret: apiSecret,
                discord: discordUrl
            }));
            
            alert("Paramètres mis à jour !");
        });
    }

    // 7. Backtest
    const btnRunBacktest = document.getElementById("btn-run-backtest");
    if(btnRunBacktest) {
        btnRunBacktest.addEventListener("click", () => {
            const resDiv = document.getElementById("backtest-results");
            if(resDiv) resDiv.innerHTML = `<p class="text-muted"><i class="lucide-refresh-cw" style="animation: spin 2s linear infinite;"></i> Backtest en cours...</p>`;
            ws.send(JSON.stringify({ command: "run_backtest" }));
        });
    }
});
