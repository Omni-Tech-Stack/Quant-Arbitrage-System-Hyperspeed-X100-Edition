/**
 * Notification Integration Module
 * Implements Telegram and Discord notifications using .env configuration
 */

const axios = require('axios');
const { envConfig } = require('./env-config');

class NotificationIntegration {
  constructor() {
    this.config = null;
    this.initialized = false;
    this.channels = new Map();
  }

  /**
   * Initialize notification channels from environment config
   */
  initialize() {
    if (this.initialized) {
      return { success: true, message: 'Already initialized' };
    }

    // Load environment config
    if (!envConfig.loaded) {
      envConfig.load();
    }

    this.config = envConfig.getNotificationConfig();

    // Initialize each notification channel
    this._initializeTelegram();
    this._initializeDiscord();

    this.initialized = true;

    return {
      success: true,
      activeChannels: this.channels.size,
      channels: Array.from(this.channels.keys())
    };
  }

  /**
   * Initialize Telegram bot
   */
  _initializeTelegram() {
    const { telegram } = this.config;
    
    if (!telegram.botToken || !telegram.chatId) {
      return;
    }

    this.channels.set('TELEGRAM', {
      name: 'Telegram',
      type: 'Bot',
      botToken: telegram.botToken,
      chatId: telegram.chatId,
      baseUrl: `https://api.telegram.org/bot${telegram.botToken}`,
      send: async (message, options = {}) => {
        return this._sendTelegramMessage(message, options);
      }
    });
  }

  /**
   * Initialize Discord webhook
   */
  _initializeDiscord() {
    const { discord } = this.config;
    
    if (!discord.webhookUrl) {
      return;
    }

    this.channels.set('DISCORD', {
      name: 'Discord',
      type: 'Webhook',
      webhookUrl: discord.webhookUrl,
      send: async (message, options = {}) => {
        return this._sendDiscordMessage(message, options);
      }
    });
  }

  /**
   * Send message via Telegram
   */
  async _sendTelegramMessage(message, options = {}) {
    if (!this.channels.has('TELEGRAM')) {
      return { success: false, error: 'Telegram not configured' };
    }

    const channel = this.channels.get('TELEGRAM');
    const {
      parseMode = 'HTML',
      disableNotification = false,
      disableWebPagePreview = true
    } = options;

    try {
      const url = `${channel.baseUrl}/sendMessage`;
      
      const response = await axios.post(url, {
        chat_id: channel.chatId,
        text: message,
        parse_mode: parseMode,
        disable_notification: disableNotification,
        disable_web_page_preview: disableWebPagePreview
      });

      if (!response.data.ok) {
        return {
          success: false,
          error: response.data.description || 'Unknown error',
          channel: 'Telegram'
        };
      }

      return {
        success: true,
        messageId: response.data.result.message_id,
        channel: 'Telegram'
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        channel: 'Telegram'
      };
    }
  }

  /**
   * Send message via Discord
   */
  async _sendDiscordMessage(message, options = {}) {
    if (!this.channels.has('DISCORD')) {
      return { success: false, error: 'Discord not configured' };
    }

    const channel = this.channels.get('DISCORD');
    const {
      username = 'Arbitrage Bot',
      embeds = null,
      avatarUrl = null
    } = options;

    try {
      const payload = {
        content: message,
        username
      };

      if (embeds) {
        payload.embeds = embeds;
      }

      if (avatarUrl) {
        payload.avatar_url = avatarUrl;
      }

      await axios.post(channel.webhookUrl, payload);

      return {
        success: true,
        channel: 'Discord'
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        channel: 'Discord'
      };
    }
  }

  /**
   * Send notification to all configured channels
   */
  async notify(message, options = {}) {
    if (!this.initialized) {
      this.initialize();
    }

    if (this.channels.size === 0) {
      return {
        success: false,
        error: 'No notification channels configured'
      };
    }

    const results = [];

    for (const [channelName, channel] of this.channels) {
      const result = await channel.send(message, options);
      results.push({ channel: channelName, ...result });
    }

    const successful = results.filter(r => r.success).length;

    return {
      success: successful > 0,
      totalChannels: this.channels.size,
      successful,
      failed: this.channels.size - successful,
      results
    };
  }

  /**
   * Send arbitrage opportunity notification
   */
  async notifyArbitrageOpportunity(opportunity) {
    const message = this._formatArbitrageOpportunity(opportunity);
    return this.notify(message, { parseMode: 'HTML' });
  }

  /**
   * Send trade execution notification
   */
  async notifyTradeExecution(trade) {
    const message = this._formatTradeExecution(trade);
    return this.notify(message, { parseMode: 'HTML' });
  }

  /**
   * Send error notification
   */
  async notifyError(error, context = '') {
    const message = this._formatError(error, context);
    return this.notify(message, { parseMode: 'HTML' });
  }

  /**
   * Send system status notification
   */
  async notifySystemStatus(status) {
    const message = this._formatSystemStatus(status);
    return this.notify(message, { parseMode: 'HTML' });
  }

  /**
   * Format arbitrage opportunity message
   */
  _formatArbitrageOpportunity(opp) {
    return `
🎯 <b>Arbitrage Opportunity Detected</b>

💰 <b>Profit:</b> $${opp.profitUSD?.toFixed(2) || 'N/A'}
📊 <b>Profit %:</b> ${opp.profitPercent?.toFixed(2) || 'N/A'}%

🔀 <b>Route:</b>
  ${opp.buyExchange} → ${opp.sellExchange}
  ${opp.tokenIn} → ${opp.tokenOut}

💵 <b>Amount:</b> ${opp.amount || 'N/A'}
⛽ <b>Gas Estimate:</b> ${opp.gasEstimate || 'N/A'} Gwei

⏰ <b>Detected:</b> ${new Date().toLocaleString()}
    `.trim();
  }

  /**
   * Format trade execution message
   */
  _formatTradeExecution(trade) {
    const statusEmoji = trade.success ? '✅' : '❌';
    
    return `
${statusEmoji} <b>Trade ${trade.success ? 'Executed' : 'Failed'}</b>

💰 <b>Profit:</b> ${trade.actualProfit ? `$${trade.actualProfit.toFixed(2)}` : 'N/A'}
🔗 <b>TX Hash:</b> <code>${trade.txHash || 'N/A'}</code>

🔀 <b>Route:</b>
  ${trade.route || 'N/A'}

⛽ <b>Gas Used:</b> ${trade.gasUsed || 'N/A'}
💵 <b>Gas Price:</b> ${trade.gasPrice || 'N/A'} Gwei

⏰ <b>Time:</b> ${new Date().toLocaleString()}
    `.trim();
  }

  /**
   * Format error message
   */
  _formatError(error, context) {
    return `
🚨 <b>Error Alert</b>

⚠️ <b>Context:</b> ${context || 'Unknown'}
❌ <b>Error:</b> ${error.message || error}

📋 <b>Stack:</b>
<code>${error.stack?.substring(0, 200) || 'No stack trace'}</code>

⏰ <b>Time:</b> ${new Date().toLocaleString()}
    `.trim();
  }

  /**
   * Format system status message
   */
  _formatSystemStatus(status) {
    return `
📊 <b>System Status Update</b>

🟢 <b>Status:</b> ${status.online ? 'Online' : 'Offline'}
⚡ <b>Uptime:</b> ${status.uptime || 'N/A'}

📈 <b>Stats:</b>
  Opportunities: ${status.opportunitiesDetected || 0}
  Trades: ${status.tradesExecuted || 0}
  Success Rate: ${status.successRate || 0}%

💰 <b>Profit:</b>
  Total: $${status.totalProfit?.toFixed(2) || '0.00'}
  Today: $${status.todayProfit?.toFixed(2) || '0.00'}

⏰ <b>Updated:</b> ${new Date().toLocaleString()}
    `.trim();
  }

  /**
   * Test notification channels
   */
  async test() {
    if (!this.initialized) {
      this.initialize();
    }

    if (this.channels.size === 0) {
      return {
        success: false,
        error: 'No notification channels configured'
      };
    }

    const testMessage = `
🧪 <b>Test Notification</b>

This is a test message from the Quant Arbitrage System.

⏰ ${new Date().toLocaleString()}
    `.trim();

    return this.notify(testMessage, { parseMode: 'HTML' });
  }

  /**
   * Get available channels
   */
  getAvailableChannels() {
    if (!this.initialized) {
      this.initialize();
    }

    return Array.from(this.channels.entries()).map(([key, value]) => ({
      id: key,
      name: value.name,
      type: value.type
    }));
  }

  /**
   * Print summary
   */
  printSummary() {
    console.log('\n╔═══════════════════════════════════════════════════════════╗');
    console.log('║          NOTIFICATION INTEGRATION SUMMARY                 ║');
    console.log('╚═══════════════════════════════════════════════════════════╝\n');

    if (!this.initialized) {
      console.log('❌ Not initialized. Call initialize() first.\n');
      return;
    }

    console.log(`Total notification channels: ${this.channels.size}\n`);

    if (this.channels.size > 0) {
      console.log('Configured Channels:');
      console.log('─'.repeat(60));
      
      for (const channel of this.channels.values()) {
        console.log(`  ✓ ${channel.name.padEnd(20)} ${channel.type}`);
      }
    } else {
      console.log('⚠️  No notification channels configured');
    }

    console.log('\n');
  }
}

// Export singleton instance
const notificationIntegration = new NotificationIntegration();

module.exports = {
  NotificationIntegration,
  notificationIntegration
};
