#!/usr/bin/env python3
"""
Dependency Verification Script
Checks all required dependencies for the Quant Arbitrage System
"""

import sys
import subprocess
from typing import List, Tuple

# Colors for output
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def check_package(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """
    Check if a Python package is installed and importable
    
    Args:
        package_name: pip package name
        import_name: import name (if different from package_name)
    
    Returns:
        Tuple of (is_installed, version_or_error)
    """
    if import_name is None:
        import_name = package_name
    
    try:
        module = __import__(import_name)
        version = getattr(module, '__version__', 'unknown')
        return True, version
    except ImportError as e:
        return False, str(e)


def print_header(text: str):
    """Print section header"""
    print(f"\n{BLUE}{'=' * 80}{NC}")
    print(f"{BLUE}  {text}{NC}")
    print(f"{BLUE}{'=' * 80}{NC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✓{NC} {text}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗{NC} {text}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠{NC} {text}")


def main():
    """Main verification routine"""
    print_header("DEPENDENCY VERIFICATION - QUANT ARBITRAGE SYSTEM")
    
    # Core dependencies
    core_packages = [
        ('numpy', 'numpy'),
        ('pandas', 'pandas'),
    ]
    
    # ML dependencies for Dual AI system
    ml_packages = [
        ('scikit-learn', 'sklearn'),
        ('xgboost', 'xgboost'),
        ('joblib', 'joblib'),
    ]
    
    # ONNX dependencies
    onnx_packages = [
        ('onnx', 'onnx'),
        ('onnxruntime', 'onnxruntime'),
        ('skl2onnx', 'skl2onnx'),
    ]
    
    # Web3 and blockchain dependencies (required for live trading)
    web3_packages = [
        ('web3', 'web3'),
        ('eth-account', 'eth_account'),
        ('eth-utils', 'eth_utils'),
    ]
    
    # Configuration dependencies (required)
    config_packages = [
        ('python-dotenv', 'dotenv'),
    ]
    
    # Testing dependencies (recommended)
    test_packages = [
        ('pytest', 'pytest'),
        ('pytest-asyncio', 'pytest_asyncio'),
    ]
    
    # Optional dependencies
    optional_packages = [
        ('aiohttp', 'aiohttp'),
        ('pyyaml', 'yaml'),
        ('prometheus-client', 'prometheus_client'),
    ]
    
    all_ok = True
    missing_packages = []
    
    # Check core dependencies
    print("Checking core dependencies:")
    for package, import_name in core_packages:
        installed, version = check_package(package, import_name)
        if installed:
            print_success(f"{package} {version}")
        else:
            print_error(f"{package} NOT INSTALLED")
            missing_packages.append(package)
            all_ok = False
    
    # Check ML dependencies
    print("\nChecking ML dependencies (required for Dual AI):")
    ml_ok = True
    for package, import_name in ml_packages:
        installed, version = check_package(package, import_name)
        if installed:
            print_success(f"{package} {version}")
        else:
            print_error(f"{package} NOT INSTALLED")
            missing_packages.append(package)
            ml_ok = False
    
    # Check ONNX dependencies
    print("\nChecking ONNX dependencies (required for Dual AI):")
    onnx_ok = True
    for package, import_name in onnx_packages:
        installed, version = check_package(package, import_name)
        if installed:
            print_success(f"{package} {version}")
        else:
            print_error(f"{package} NOT INSTALLED")
            missing_packages.append(package)
            onnx_ok = False
    
    # Check Web3 dependencies
    print("\nChecking Web3 dependencies (required for live trading):")
    web3_ok = True
    for package, import_name in web3_packages:
        installed, version = check_package(package, import_name)
        if installed:
            print_success(f"{package} {version}")
        else:
            print_error(f"{package} NOT INSTALLED")
            missing_packages.append(package)
            web3_ok = False
    
    # Check configuration dependencies
    print("\nChecking configuration dependencies (required):")
    config_ok = True
    for package, import_name in config_packages:
        installed, version = check_package(package, import_name)
        if installed:
            print_success(f"{package} {version}")
        else:
            print_error(f"{package} NOT INSTALLED")
            missing_packages.append(package)
            config_ok = False
    
    # Check testing dependencies
    print("\nChecking testing dependencies (recommended):")
    test_ok = True
    for package, import_name in test_packages:
        installed, version = check_package(package, import_name)
        if installed:
            print_success(f"{package} {version}")
        else:
            print_warning(f"{package} not installed (recommended for development)")
            test_ok = False
    
    # Check optional dependencies
    print("\nChecking optional dependencies:")
    for package, import_name in optional_packages:
        installed, version = check_package(package, import_name)
        if installed:
            print_success(f"{package} {version} (optional)")
        else:
            print_warning(f"{package} not installed (optional)")
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    if all_ok and ml_ok and onnx_ok and web3_ok and config_ok:
        print_success("All required dependencies are installed!")
        print_success("Dual AI system is ready to use")
        print_success("Web3 integration is ready for live trading")
        if not test_ok:
            print_warning("Consider installing testing dependencies for development")
        return 0
    else:
        if missing_packages:
            print_error("Missing required packages:")
            for package in missing_packages:
                print(f"  - {package}")
            
            print(f"\n{YELLOW}To install missing packages, run:{NC}")
            print(f"  pip3 install {' '.join(missing_packages)}")
            print(f"\n{YELLOW}Or install all requirements:{NC}")
            print(f"  pip3 install -r requirements.txt")
        
        if not ml_ok or not onnx_ok:
            print_warning("\nDual AI system will NOT work without ML/ONNX dependencies")
            print_warning("Install them to enable advanced model features")
        
        if not web3_ok:
            print_warning("\nWeb3 integration will NOT work without web3 dependencies")
            print_warning("Install them to enable live trading on blockchain")
        
        if not config_ok:
            print_warning("\nConfiguration management will NOT work properly")
            print_warning("Install python-dotenv for .env file support")
        
        return 1


if __name__ == '__main__':
    sys.exit(main())
