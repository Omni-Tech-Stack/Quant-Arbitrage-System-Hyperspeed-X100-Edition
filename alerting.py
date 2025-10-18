#!/usr/bin/env python3
"""
Alerting System for Anomaly Detection and Critical Events
Supports multiple notification channels: logging, console, file, and extensible to external services
"""

import time
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Callable
from collections import deque

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertChannel(Enum):
    """Available alert channels"""
    CONSOLE = "console"
    FILE = "file"
    LOG = "log"
    # Future integrations:
    # PAGERDUTY = "pagerduty"
    # OPSGENIE = "opsgenie"
    # SLACK = "slack"
    # EMAIL = "email"
    # WEBHOOK = "webhook"

class AlertingSystem:
    """
    Comprehensive alerting system for monitoring and anomaly detection
    """
    
    def __init__(self, alert_file: str = "logs/alerts.log"):
        self.alert_file = alert_file
        self.alert_history = deque(maxlen=1000)
        self.alert_counts = {severity: 0 for severity in AlertSeverity}
        self.suppression_rules = {}  # Alert suppression to avoid spam
        
        # Alert thresholds
        self.thresholds = {
            "success_rate_low": 70.0,  # Alert if success rate < 70%
            "error_rate_high": 10.0,   # Alert if error rate > 10%
            "profit_negative_hours": 4,  # Alert if negative profit for 4 hours
            "gas_price_spike": 200,     # Alert if gas > 200 gwei
            "slippage_high": 5.0,       # Alert if slippage > 5%
            "latency_high_ms": 5000,    # Alert if latency > 5 seconds
            "loss_per_trade": 500,      # Alert if single trade loss > $500
            "circuit_breaker_trigger": True,  # Alert on circuit breaker
            "failed_trades_consecutive": 5,  # Alert after 5 consecutive failures
        }
        
        # Enabled channels
        self.enabled_channels = {
            AlertChannel.CONSOLE,
            AlertChannel.FILE,
            AlertChannel.LOG
        }
        
        # Custom alert handlers (for external integrations)
        self.custom_handlers: Dict[str, Callable] = {}
        
        logger.info("AlertingSystem initialized")
    
    def send_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.WARNING,
        context: Optional[Dict] = None,
        channels: Optional[List[AlertChannel]] = None
    ) -> bool:
        """
        Send an alert through specified channels
        
        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity level
            context: Additional context data
            channels: Specific channels to use (defaults to all enabled)
            
        Returns:
            bool: True if alert was sent successfully
        """
        # Check suppression
        if self._is_suppressed(title):
            logger.debug(f"Alert suppressed: {title}")
            return False
        
        # Build alert object
        alert = {
            "title": title,
            "message": message,
            "severity": severity.value,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        # Store in history
        self.alert_history.append(alert)
        self.alert_counts[severity] += 1
        
        # Determine channels
        if channels is None:
            channels = list(self.enabled_channels)
        
        # Send through each channel
        success = True
        for channel in channels:
            if channel in self.enabled_channels:
                try:
                    self._send_to_channel(channel, alert)
                except Exception as e:
                    logger.error(f"Failed to send alert to {channel}: {e}")
                    success = False
        
        # Update suppression
        self._update_suppression(title)
        
        return success
    
    def _send_to_channel(self, channel: AlertChannel, alert: Dict):
        """Send alert to specific channel"""
        formatted = self._format_alert(alert)
        
        if channel == AlertChannel.CONSOLE:
            self._send_to_console(formatted, alert)
        
        elif channel == AlertChannel.FILE:
            self._send_to_file(formatted, alert)
        
        elif channel == AlertChannel.LOG:
            self._send_to_log(formatted, alert)
        
        # Call custom handlers if registered
        handler_name = channel.value
        if handler_name in self.custom_handlers:
            self.custom_handlers[handler_name](alert)
    
    def _format_alert(self, alert: Dict) -> str:
        """Format alert for display"""
        severity = alert["severity"].upper()
        icon = self._get_severity_icon(severity)
        
        formatted = f"""
{icon} {severity} ALERT {icon}
────────────────────────────────────────────────
Title:     {alert['title']}
Message:   {alert['message']}
Timestamp: {alert['timestamp']}
"""
        if alert.get("context"):
            formatted += f"Context:   {json.dumps(alert['context'], indent=11)}\n"
        
        formatted += "────────────────────────────────────────────────"
        return formatted
    
    def _get_severity_icon(self, severity: str) -> str:
        """Get emoji icon for severity"""
        icons = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🚨"
        }
        return icons.get(severity, "•")
    
    def _send_to_console(self, formatted: str, alert: Dict):
        """Send alert to console"""
        print(formatted)
    
    def _send_to_file(self, formatted: str, alert: Dict):
        """Send alert to file"""
        with open(self.alert_file, 'a') as f:
            f.write(formatted + "\n\n")
    
    def _send_to_log(self, formatted: str, alert: Dict):
        """Send alert to logging system"""
        severity = alert["severity"]
        if severity == "critical":
            logger.critical(alert["message"], extra=alert)
        elif severity == "error":
            logger.error(alert["message"], extra=alert)
        elif severity == "warning":
            logger.warning(alert["message"], extra=alert)
        else:
            logger.info(alert["message"], extra=alert)
    
    def _is_suppressed(self, title: str) -> bool:
        """Check if alert should be suppressed to avoid spam"""
        if title not in self.suppression_rules:
            return False
        
        last_sent, count = self.suppression_rules[title]
        elapsed = time.time() - last_sent
        
        # Suppress if sent within last 5 minutes and count > 10
        if elapsed < 300 and count > 10:
            return True
        
        return False
    
    def _update_suppression(self, title: str):
        """Update suppression tracking"""
        current_time = time.time()
        
        if title in self.suppression_rules:
            last_sent, count = self.suppression_rules[title]
            elapsed = current_time - last_sent
            
            # Reset count if enough time has passed
            if elapsed > 300:  # 5 minutes
                self.suppression_rules[title] = (current_time, 1)
            else:
                self.suppression_rules[title] = (last_sent, count + 1)
        else:
            self.suppression_rules[title] = (current_time, 1)
    
    def check_metrics_and_alert(self, metrics: Dict):
        """
        Check metrics against thresholds and generate alerts
        
        Args:
            metrics: Metrics dictionary from ObservabilityMetrics
        """
        # Check success rate
        success_rate = metrics.get("success_rate_percent", 100)
        if success_rate < self.thresholds["success_rate_low"]:
            self.send_alert(
                "Low Success Rate",
                f"Success rate dropped to {success_rate:.1f}% (threshold: {self.thresholds['success_rate_low']}%)",
                AlertSeverity.WARNING,
                {"success_rate": success_rate}
            )
        
        # Check error rate
        errors = metrics.get("errors", {})
        error_rate = errors.get("error_rate_percent", 0)
        if error_rate > self.thresholds["error_rate_high"]:
            self.send_alert(
                "High Error Rate",
                f"Error rate increased to {error_rate:.1f}% (threshold: {self.thresholds['error_rate_high']}%)",
                AlertSeverity.ERROR,
                {"error_rate": error_rate, "errors": errors}
            )
        
        # Check gas prices
        gas_metrics = metrics.get("gas", {})
        max_gas = gas_metrics.get("max_gas_price_gwei", 0)
        if max_gas > self.thresholds["gas_price_spike"]:
            self.send_alert(
                "Gas Price Spike",
                f"Gas price spiked to {max_gas} gwei (threshold: {self.thresholds['gas_price_spike']} gwei)",
                AlertSeverity.WARNING,
                {"gas_price": max_gas}
            )
        
        # Check for anomalies
        anomalies = metrics.get("anomalies", {})
        recent_anomalies = anomalies.get("recent", [])
        for anomaly in recent_anomalies:
            if anomaly.get("type") == "high_slippage":
                self.send_alert(
                    "High Slippage Detected",
                    f"Trade experienced {anomaly.get('value', 0):.2f}% slippage",
                    AlertSeverity.WARNING,
                    anomaly
                )
            elif anomaly.get("type") == "high_gas_cost":
                self.send_alert(
                    "High Gas Cost",
                    f"Trade gas cost: ${anomaly.get('value', 0):.2f}",
                    AlertSeverity.WARNING,
                    anomaly
                )
    
    def alert_circuit_breaker_triggered(self, reason: str, context: Dict = None):
        """Alert when circuit breaker is triggered"""
        self.send_alert(
            "Circuit Breaker Triggered",
            f"Trading halted due to: {reason}",
            AlertSeverity.CRITICAL,
            context
        )
    
    def alert_emergency_shutdown(self, reason: str, context: Dict = None):
        """Alert on emergency shutdown"""
        self.send_alert(
            "EMERGENCY SHUTDOWN",
            f"System emergency shutdown activated: {reason}",
            AlertSeverity.CRITICAL,
            context
        )
    
    def alert_large_loss(self, amount: float, trade_id: str, context: Dict = None):
        """Alert on large loss"""
        self.send_alert(
            "Large Loss Detected",
            f"Trade {trade_id} resulted in ${amount:.2f} loss",
            AlertSeverity.ERROR,
            context
        )
    
    def alert_consecutive_failures(self, count: int, context: Dict = None):
        """Alert on consecutive trade failures"""
        self.send_alert(
            "Consecutive Trade Failures",
            f"{count} consecutive trades have failed",
            AlertSeverity.ERROR,
            context
        )
    
    def register_custom_handler(self, channel_name: str, handler: Callable):
        """
        Register a custom alert handler for external integrations
        
        Example:
            def send_to_slack(alert):
                # Send alert to Slack
                pass
            
            alerting.register_custom_handler("slack", send_to_slack)
        """
        self.custom_handlers[channel_name] = handler
        logger.info(f"Registered custom alert handler: {channel_name}")
    
    def enable_channel(self, channel: AlertChannel):
        """Enable an alert channel"""
        self.enabled_channels.add(channel)
    
    def disable_channel(self, channel: AlertChannel):
        """Disable an alert channel"""
        self.enabled_channels.discard(channel)
    
    def get_alert_summary(self) -> Dict:
        """Get summary of alerts"""
        return {
            "total_alerts": len(self.alert_history),
            "by_severity": {
                severity.value: count 
                for severity, count in self.alert_counts.items()
            },
            "recent_alerts": list(self.alert_history)[-10:],
            "enabled_channels": [ch.value for ch in self.enabled_channels]
        }

# Global alerting instance
_global_alerting = None

def get_alerting():
    """Get global alerting instance"""
    global _global_alerting
    if _global_alerting is None:
        _global_alerting = AlertingSystem()
    return _global_alerting

# Integration examples for external services (to be implemented as needed)
def send_to_pagerduty(alert: Dict):
    """Send alert to PagerDuty (placeholder for implementation)"""
    # Requires PagerDuty API integration
    # from pypd import EventV2
    # EventV2.create(data={
    #     'routing_key': 'YOUR_INTEGRATION_KEY',
    #     'event_action': 'trigger',
    #     'payload': {
    #         'summary': alert['title'],
    #         'severity': alert['severity'],
    #         'source': 'arbitrage-system'
    #     }
    # })
    logger.info("PagerDuty integration not yet implemented")

def send_to_opsgenie(alert: Dict):
    """Send alert to Opsgenie (placeholder for implementation)"""
    # Requires Opsgenie API integration
    logger.info("Opsgenie integration not yet implemented")

def send_to_slack(alert: Dict):
    """Send alert to Slack (placeholder for implementation)"""
    # Requires Slack webhook integration
    # import requests
    # webhook_url = "YOUR_SLACK_WEBHOOK_URL"
    # requests.post(webhook_url, json={
    #     'text': f"{alert['title']}\n{alert['message']}"
    # })
    logger.info("Slack integration not yet implemented")

if __name__ == "__main__":
    # Test the alerting system
    print("Testing Alerting System\n")
    print("=" * 80)
    
    alerting = AlertingSystem()
    
    # Test different severity levels
    alerting.send_alert(
        "System Initialized",
        "Arbitrage system has started successfully",
        AlertSeverity.INFO
    )
    
    alerting.send_alert(
        "High Slippage Detected",
        "Trade experienced 6.5% slippage on Uniswap",
        AlertSeverity.WARNING,
        {"slippage": 6.5, "dex": "uniswap"}
    )
    
    alerting.send_alert(
        "Trade Execution Failed",
        "Failed to execute trade due to insufficient liquidity",
        AlertSeverity.ERROR,
        {"trade_id": "12345", "reason": "insufficient_liquidity"}
    )
    
    alerting.send_alert(
        "CIRCUIT BREAKER TRIGGERED",
        "Maximum hourly loss limit reached",
        AlertSeverity.CRITICAL,
        {"loss": 2500, "limit": 2000}
    )
    
    print("\n" + "=" * 80)
    print("Alert Summary:")
    print("=" * 80)
    print(json.dumps(alerting.get_alert_summary(), indent=2))
