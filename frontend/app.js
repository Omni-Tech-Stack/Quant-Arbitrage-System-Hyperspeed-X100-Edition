// Configuration
const API_URL = 'http://localhost:3001';
const WS_URL = 'ws://localhost:3001';

// State
let ws = null;
let reconnectInterval = null;

// DOM Elements
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const totalTradesEl = document.getElementById('totalTrades');
const successRateEl = document.getElementById('successRate');
const totalProfitEl = document.getElementById('totalProfit');
const avgSlippageEl = document.getElementById('avgSlippage');
const opportunitiesBody = document.getElementById('opportunitiesBody');
const tradesBody = document.getElementById('tradesBody');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard initializing...');
    connectWebSocket();
    fetchInitialData();
});

// WebSocket Connection
function connectWebSocket() {
    try {
        ws = new WebSocket(WS_URL);
        
        ws.onopen = () => {
            console.log('WebSocket connected');
            updateStatus('connected', 'Connected');
            if (reconnectInterval) {
                clearInterval(reconnectInterval);
                reconnectInterval = null;
            }
        };
        
        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                handleWebSocketMessage(message);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateStatus('error', 'Connection Error');
        };
        
        ws.onclose = () => {
            console.log('WebSocket disconnected');
            updateStatus('disconnected', 'Disconnected');
            
            // Attempt to reconnect
            if (!reconnectInterval) {
                reconnectInterval = setInterval(() => {
                    console.log('Attempting to reconnect...');
                    connectWebSocket();
                }, 5000);
            }
        };
    } catch (error) {
        console.error('Failed to create WebSocket:', error);
        updateStatus('error', 'Connection Failed');
    }
}

// Handle WebSocket Messages
function handleWebSocketMessage(message) {
    switch (message.type) {
        case 'initial':
            updateDashboard(message.data);
            break;
        case 'opportunity':
            addOpportunity(message.data);
            break;
        case 'trade':
            addTrade(message.data);
            break;
        case 'stats':
            updateStats(message.data);
            break;
        default:
            console.log('Unknown message type:', message.type);
    }
}

// Fetch Initial Data via REST API
async function fetchInitialData() {
    try {
        const [stats, opportunities, trades] = await Promise.all([
            fetch(`${API_URL}/api/stats`).then(r => r.json()),
            fetch(`${API_URL}/api/opportunities`).then(r => r.json()),
            fetch(`${API_URL}/api/trades?limit=20`).then(r => r.json())
        ]);
        
        updateStats(stats);
        opportunities.forEach(addOpportunity);
        trades.forEach(addTrade);
    } catch (error) {
        console.error('Error fetching initial data:', error);
    }
}

// Update Dashboard
function updateDashboard(data) {
    updateStats(data.stats);
    
    opportunitiesBody.innerHTML = '';
    data.opportunities.forEach(addOpportunity);
    
    tradesBody.innerHTML = '';
    data.trades.slice(-20).forEach(addTrade);
}

// Update Statistics
function updateStats(stats) {
    totalTradesEl.textContent = stats.totalTrades;
    
    const successRate = stats.totalTrades > 0 
        ? (stats.successfulTrades / stats.totalTrades * 100).toFixed(1)
        : 0;
    successRateEl.textContent = `${successRate}%`;
    
    totalProfitEl.textContent = `$${stats.totalProfit.toFixed(2)}`;
    avgSlippageEl.textContent = `${stats.avgSlippage.toFixed(4)}%`;
}

// Add Opportunity to Table
function addOpportunity(opportunity) {
    if (opportunitiesBody.querySelector('.no-data')) {
        opportunitiesBody.innerHTML = '';
    }
    
    const row = document.createElement('tr');
    row.className = 'fade-in';
    
    const confidence = parseFloat(opportunity.confidence);
    const confidenceClass = confidence >= 85 ? 'confidence-high' : 
                           confidence >= 70 ? 'confidence-medium' : 'confidence-low';
    
    row.innerHTML = `
        <td class="time-cell">${formatTime(opportunity.timestamp)}</td>
        <td>${opportunity.pool1}</td>
        <td>${opportunity.pool2}</td>
        <td>${opportunity.pair}</td>
        <td class="profit-positive">$${opportunity.expectedProfit}</td>
        <td>${opportunity.slippage}%</td>
        <td class="${confidenceClass}">${opportunity.confidence}%</td>
    `;
    
    opportunitiesBody.insertBefore(row, opportunitiesBody.firstChild);
    
    // Keep only last 20 opportunities
    while (opportunitiesBody.children.length > 20) {
        opportunitiesBody.removeChild(opportunitiesBody.lastChild);
    }
}

// Add Trade to Table
function addTrade(trade) {
    if (tradesBody.querySelector('.no-data')) {
        tradesBody.innerHTML = '';
    }
    
    const row = document.createElement('tr');
    row.className = 'fade-in';
    
    const statusClass = trade.success ? 'status-success' : 'status-failed';
    const profitClass = trade.profit > 0 ? 'profit-positive' : 'profit-negative';
    
    row.innerHTML = `
        <td class="time-cell">${formatTime(trade.timestamp)}</td>
        <td>${trade.pool1}</td>
        <td>${trade.pool2}</td>
        <td>${trade.pair}</td>
        <td class="${statusClass}">${trade.success ? '✓ Success' : '✗ Failed'}</td>
        <td class="${profitClass}">$${trade.profit.toFixed(2)}</td>
        <td>${trade.actualSlippage.toFixed(4)}%</td>
        <td>${parseInt(trade.gasUsed).toLocaleString()}</td>
    `;
    
    tradesBody.insertBefore(row, tradesBody.firstChild);
    
    // Keep only last 20 trades
    while (tradesBody.children.length > 20) {
        tradesBody.removeChild(tradesBody.lastChild);
    }
}

// Update Status Indicator
function updateStatus(status, text) {
    statusText.textContent = text;
    
    if (status === 'connected') {
        statusDot.classList.add('connected');
    } else {
        statusDot.classList.remove('connected');
    }
}

// Format Timestamp
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit' 
    });
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (ws) {
        ws.close();
    }
    if (reconnectInterval) {
        clearInterval(reconnectInterval);
    }
});
