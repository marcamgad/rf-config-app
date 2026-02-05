#!/bin/bash
# RF Config Sender - Linux Python Bootstrap Installer

echo "============================================================"
echo "Checking System Requirements..."
echo "============================================================"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 is NOT installed."
    
    # Check for apt-get (Debian/Ubuntu)
    if command -v apt-get &> /dev/null; then
        echo "[*] Detected Debian/Ubuntu system."
        echo "[*] Attempting to install Python 3..."
        
        sudo apt-get update
        sudo apt-get install -y python3 python3-venv python3-pip
        
        if [ $? -ne 0 ]; then
            echo "[X] Failed to install Python 3. Please install it manually."
            exit 1
        fi
    else
        echo "[X] Unsupported Linux distribution for auto-install."
        echo "    Please install Python 3 manually using your package manager."
        echo "    (yum, dnf, pacman, etc.)"
        exit 1
    fi
else
    echo "[*] Python 3 is already installed."
    
    # Check for venv (often separate on Debian/Ubuntu)
    dpkg -s python3-venv &> /dev/null
    if [ $? -eq 0 ]; then
        echo "[*] python3-venv is present."
    elif command -v apt-get &> /dev/null; then
         # Try to be safe, sometimes command -v python3 works but venv module is missing
         echo "[!] Checking for venv module..."
         python3 -m venv --help > /dev/null 2>&1
         if [ $? -ne 0 ]; then
             echo "[!] python3-venv module missing. Installing..."
             sudo apt-get install -y python3-venv
         fi
    fi
fi

echo ""
echo "============================================================"
echo "Launching RF Config Installer..."
echo "============================================================"
python3 install.py
