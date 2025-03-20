#!/usr/bin/env python
# BitNet Installer for Windows
# Modern Python-based installer with progress bars and error handling

import os
import sys
import shutil
import logging
import subprocess
import tempfile
import platform
import time
import json
from pathlib import Path
from datetime import datetime
import ctypes
import threading

# Try to import UI libraries, install if missing
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    import tqdm
except ImportError:
    print("Installing required dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"])
    try:
        import tqdm
    except ImportError:
        print("Failed to install dependencies. Please run: pip install tqdm")
        sys.exit(1)

# Constants
VERSION = "1.0.0"
TITLE = f"BitNet Installer v{VERSION}"
BITNET_REPO = "https://github.com/microsoft/BitNet.git"
APP_DATA = os.path.join(os.environ["LOCALAPPDATA"], "BitNet")
LOG_FILE = os.path.join(APP_DATA, "bitnet_install.log")
TEMP_DIR = os.path.join(tempfile.gettempdir(), "bitnet_temp")

# Ensure app data directory exists
os.makedirs(APP_DATA, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("BitNet")

# Configuration
CONFIG_FILE = os.path.join(APP_DATA, "config.json")
DEFAULT_CONFIG = {
    "install_dir": os.path.join(os.path.expanduser("~"), "BitNet"),
    "conda_path": "",
    "git_path": "",
    "vs_path": "",
    "enable_gpu": True,
    "create_shortcut": True,
    "first_run": True
}

def is_admin():
    """Check if the script is running with admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def load_config():
    """Load configuration or create default if not exists"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Update with any new keys from default config
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
    
    # Create default config
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Failed to save config: {str(e)}")
        return False

# This module will be extended with the actual installation functions and UI
if __name__ == "__main__":
    print(f"BitNet Installer {VERSION} initializing...")
    if not is_admin():
        print("Warning: This installer works best with administrator privileges")
        print("Some features may not work correctly without admin rights")
    
    config = load_config()
    print(f"Configuration loaded from {CONFIG_FILE}")
    print("Run 'installer_gui.py' for the graphical installer interface")
