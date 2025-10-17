const express = require('express');
const cors = require('cors');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Middleware
app.use(cors());
app.use(express.json());

// Store for arbitrage data
const arbitrageData = {
  opportunities: [],
  trades: [],
  stats: {
    totalTrades: 0,
    successfulTrades: 0,
    totalProfit: 0,
    avgSlippage: 0
  }
};

// WebSocket connection handler
wss.on('connection', (ws) => {
  console.log('New WebSocket client connected');
  
  // Send initial data
  ws.send(JSON.stringify({
    type: 'initial',
    data: arbitrageData
  }));
  
  ws.on('close', () => {
    console.log('Client disconnected');
  });
});

// Broadcast updates to all connected clients
function broadcastUpdate(type, data) {
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify({ type, data }));
    }
  });
}

// REST API Endpoints

// Health check
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Get current arbitrage opportunities
app.get('/api/opportunities', (req, res) => {
  res.json(arbitrageData.opportunities);
});

// Get trade history
app.get('/api/trades', (req, res) => {
  const limit = parseInt(req.query.limit) || 100;
  res.json(arbitrageData.trades.slice(-limit));
});

// Get statistics
app.get('/api/stats', (req, res) => {
  res.json(arbitrageData.stats);
});

// Post new opportunity (from arbitrage engine)
app.post('/api/opportunities', (req, res) => {
  const opportunity = {
    ...req.body,
    timestamp: new Date().toISOString(),
    id: Date.now()
  };
  
  arbitrageData.opportunities.push(opportunity);
  // Keep only last 50 opportunities
  if (arbitrageData.opportunities.length > 50) {
    arbitrageData.opportunities.shift();
  }
  
  broadcastUpdate('opportunity', opportunity);
  res.json({ success: true, id: opportunity.id });
});

// Post trade execution result
app.post('/api/trades', (req, res) => {
  const trade = {
    ...req.body,
    timestamp: new Date().toISOString(),
    id: Date.now()
  };
  
  arbitrageData.trades.push(trade);
  // Keep only last 1000 trades
  if (arbitrageData.trades.length > 1000) {
    arbitrageData.trades.shift();
  }
  
  // Update statistics
  arbitrageData.stats.totalTrades++;
  if (trade.success) {
    arbitrageData.stats.successfulTrades++;
    arbitrageData.stats.totalProfit += trade.profit || 0;
  }
  
  broadcastUpdate('trade', trade);
  broadcastUpdate('stats', arbitrageData.stats);
  res.json({ success: true, id: trade.id });
});

// Simulate some data for demo purposes
function simulateData() {
  const pools = ['UniswapV2', 'UniswapV3', 'Curve', 'Balancer', 'SushiSwap'];
  const tokens = ['ETH/USDT', 'DAI/USDC', 'WBTC/ETH', 'LINK/ETH'];
  
  // Simulate opportunity every 5 seconds
  setInterval(() => {
    const opportunity = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      pool1: pools[Math.floor(Math.random() * pools.length)],
      pool2: pools[Math.floor(Math.random() * pools.length)],
      pair: tokens[Math.floor(Math.random() * tokens.length)],
      expectedProfit: (Math.random() * 100 + 10).toFixed(2),
      slippage: (Math.random() * 2).toFixed(4),
      confidence: (Math.random() * 30 + 70).toFixed(2)
    };
    
    arbitrageData.opportunities.push(opportunity);
    if (arbitrageData.opportunities.length > 50) {
      arbitrageData.opportunities.shift();
    }
    
    broadcastUpdate('opportunity', opportunity);
  }, 5000);
  
  // Simulate trade execution every 10 seconds
  setInterval(() => {
    if (arbitrageData.opportunities.length > 0) {
      const opp = arbitrageData.opportunities[Math.floor(Math.random() * arbitrageData.opportunities.length)];
      const success = Math.random() > 0.2; // 80% success rate
      
      const trade = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        opportunityId: opp.id,
        pool1: opp.pool1,
        pool2: opp.pool2,
        pair: opp.pair,
        success: success,
        profit: success ? parseFloat(opp.expectedProfit) * (0.8 + Math.random() * 0.4) : 0,
        actualSlippage: parseFloat(opp.slippage) * (0.9 + Math.random() * 0.2),
        gasUsed: (Math.random() * 200000 + 100000).toFixed(0)
      };
      
      arbitrageData.trades.push(trade);
      if (arbitrageData.trades.length > 1000) {
        arbitrageData.trades.shift();
      }
      
      // Update statistics
      arbitrageData.stats.totalTrades++;
      if (trade.success) {
        arbitrageData.stats.successfulTrades++;
        arbitrageData.stats.totalProfit += trade.profit;
      }
      arbitrageData.stats.avgSlippage = 
        arbitrageData.trades.reduce((sum, t) => sum + (t.actualSlippage || 0), 0) / 
        arbitrageData.trades.length;
      
      broadcastUpdate('trade', trade);
      broadcastUpdate('stats', arbitrageData.stats);
    }
  }, 10000);
}

// By default, system runs in ALL LIVE mode with real market data
// Set DEMO_MODE=true to enable simulated data for testing
if (process.env.DEMO_MODE === 'true') {
  console.log('Starting in DEMO mode with simulated data');
  simulateData();
} else {
  console.log('Starting in ALL LIVE mode - real market data, real volumes, real slippage, real gas fees');
  console.log('Connect your arbitrage engine to start receiving real market opportunities');
}

const PORT = process.env.PORT || 3001;

server.listen(PORT, () => {
  console.log(`Backend API server running on port ${PORT}`);
  console.log(`WebSocket server ready for real-time updates`);
});
