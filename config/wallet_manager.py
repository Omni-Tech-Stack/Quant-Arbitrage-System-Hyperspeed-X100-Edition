"""
Wallet Manager - Automatically selects correct wallet based on MODE
Wires SIM addresses to DEV/SIM modes, PRO addresses to LIVE/PRODUCTION mode
"""

import os
from typing import Dict, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('../.env')
load_dotenv('.env')  # Fallback


class WalletManager:
    """
    Manages wallet address selection based on execution mode
    
    MODE=LIVE → Uses PRO_* addresses (REAL MONEY)
    MODE=DEV/SIM → Uses SIM_* addresses (TEST ONLY)
    """
    
    def __init__(self):
        self.mode = os.getenv('MODE', 'DEV').upper()
        self.trading_mode = os.getenv('TRADING_MODE', 'DEV').upper()
        self.live_execution = os.getenv('LIVE_EXECUTION', 'false').lower() == 'true'
        
        # Production addresses (REAL MONEY - USE WITH EXTREME CAUTION)
        self.pro_executor = os.getenv('PRO_FLASHLOAN_EXECUTOR_ADDRESS')
        self.pro_bot = os.getenv('PRO_BOT_ADDRESS', '').strip('"')
        
        # Simulation/Dev addresses (SAFE FOR TESTING)
        self.sim_executor = os.getenv('SIM_FLASHLOAN_EXECUTOR_ADDRESS')
        self.sim_bot = os.getenv('SIM_BOT_ADDRESS')
        self.sim_private_key = os.getenv('SIM_PRIVATE_KEY')
        
    def is_production_mode(self) -> bool:
        """Check if we're in production mode"""
        return (
            self.mode == 'LIVE' or 
            self.trading_mode == 'LIVE' or 
            self.live_execution
        )
    
    def get_active_addresses(self) -> Dict[str, str]:
        """
        Get the active wallet addresses based on current MODE
        
        Returns:
            dict: {
                'executor': address,
                'bot': address,
                'mode': 'PRODUCTION' or 'SIMULATION',
                'private_key': key (only for SIM mode)
            }
        """
        if self.is_production_mode():
            return {
                'executor': self.pro_executor,
                'bot': self.pro_bot,
                'mode': 'PRODUCTION',
                'private_key': None,  # Never return production keys
                'warning': '⚠️  PRODUCTION MODE - REAL MONEY AT RISK'
            }
        else:
            return {
                'executor': self.sim_executor,
                'bot': self.sim_bot,
                'mode': 'SIMULATION',
                'private_key': self.sim_private_key,
                'warning': '✅ SIMULATION MODE - Safe for testing'
            }
    
    def get_executor_address(self) -> str:
        """Get the active flashloan executor address"""
        if self.is_production_mode():
            return self.pro_executor
        return self.sim_executor
    
    def get_bot_address(self) -> str:
        """Get the active bot address"""
        if self.is_production_mode():
            return self.pro_bot
        return self.sim_bot
    
    def get_private_key(self) -> str:
        """Get private key (only available in SIM mode)"""
        if self.is_production_mode():
            raise ValueError("Cannot retrieve private key in PRODUCTION mode for security")
        return self.sim_private_key
    
    def validate_configuration(self) -> Tuple[bool, str]:
        """
        Validate wallet configuration
        
        Returns:
            tuple: (is_valid, message)
        """
        addresses = self.get_active_addresses()
        
        # Check executor address
        if not addresses['executor'] or len(addresses['executor']) != 42:
            return False, f"Invalid executor address: {addresses['executor']}"
        
        # Check bot address
        if not addresses['bot'] or len(addresses['bot']) != 42:
            return False, f"Invalid bot address: {addresses['bot']}"
        
        # In SIM mode, check private key
        if not self.is_production_mode():
            if not self.sim_private_key or len(self.sim_private_key) != 66:
                return False, f"Invalid SIM private key"
        
        return True, f"✅ Wallet configuration valid for {addresses['mode']} mode"
    
    def print_configuration(self):
        """Print current wallet configuration"""
        addresses = self.get_active_addresses()
        
        print("=" * 80)
        print("  WALLET CONFIGURATION")
        print("=" * 80)
        print(f"  Mode: {self.mode}")
        print(f"  Trading Mode: {self.trading_mode}")
        print(f"  Live Execution: {self.live_execution}")
        print()
        print(f"  Active Mode: {addresses['mode']}")
        print(f"  {addresses['warning']}")
        print()
        print(f"  Executor Address: {addresses['executor']}")
        print(f"  Bot Address: {addresses['bot']}")
        
        if addresses['mode'] == 'SIMULATION' and addresses.get('private_key'):
            pk = addresses['private_key']
            print(f"  Private Key: {pk[:10]}...{pk[-4:]}")
        
        print("=" * 80)
        print()
        
        # Validation
        is_valid, message = self.validate_configuration()
        if is_valid:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
        print()


def get_wallet_config() -> Dict[str, str]:
    """
    Convenience function to get active wallet configuration
    
    Usage:
        from config.wallet_manager import get_wallet_config
        config = get_wallet_config()
        executor = config['executor']
    """
    manager = WalletManager()
    return manager.get_active_addresses()


def main():
    """Test wallet manager"""
    manager = WalletManager()
    manager.print_configuration()
    
    # Demonstrate mode switching
    print("\n" + "=" * 80)
    print("  MODE SWITCHING DEMONSTRATION")
    print("=" * 80)
    
    print("\n📋 Current addresses:")
    config = manager.get_active_addresses()
    print(f"  Executor: {config['executor']}")
    print(f"  Bot: {config['bot']}")
    print(f"  Mode: {config['mode']}")
    
    print("\n💡 To switch to PRODUCTION mode:")
    print("  1. Edit .env file")
    print("  2. Set MODE=LIVE")
    print("  3. Set LIVE_EXECUTION=true")
    print("  4. Set TRADING_MODE=LIVE")
    print("  5. Restart the system")
    
    print("\n⚠️  WARNING: Only use PRODUCTION mode when ready for REAL TRADING!")
    print()


if __name__ == "__main__":
    main()
