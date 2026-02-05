#!/usr/bin/env python3
"""
RF Config App - Full Stack Installer & Builder
==============================================

This script orchestrates the build of the full application:
1. Checks for Python and Node.js.
2. Builds the React Frontend (frontend/).
3. Copies frontend assets to the backend.
4. Installs Python dependencies.
5. Bundles everything into a single executable.

Usage:
    python install.py
"""

import sys
import os
import platform
import subprocess
import shutil
import venv

def print_step(msg):
    print("\n" + "="*60)
    print(f"[*] {msg}")
    print("="*60)

def main():
    os_type = platform.system()
    print_step(f"Detected OS: {os_type}")
    
    # 0. Check Prerequisites
    try:
        subprocess.check_call(["npm", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[*] Node.js/npm is installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[X] Node.js (npm) is NOT installed.")
        print("    Please install Node.js to build the frontend: https://nodejs.org/")
        sys.exit(1)

    if sys.version_info < (3, 6):
        print("[X] Python 3.6+ is required.")
        sys.exit(1)

    # 1. Build Frontend
    print_step("Building React Frontend...")
    
    frontend_dir = os.path.join(os.getcwd(), "frontend")
    if not os.path.exists(frontend_dir):
        print(f"[X] Frontend directory not found at: {frontend_dir}")
        sys.exit(1)
        
    try:
        # npm install
        print("[*] Installing React dependencies (npm install)...")
        shell_cmd = True if os_type == "Windows" else False
        subprocess.check_call(["npm", "install"], cwd=frontend_dir, shell=shell_cmd)
        
        # npm run build
        print("[*] Building React App (npm run build)...")
        subprocess.check_call(["npm", "run", "build"], cwd=frontend_dir, shell=shell_cmd)
    except subprocess.CalledProcessError:
        print("[X] Failed to build frontend.")
        sys.exit(1)

    # 2. Copy Assets
    print_step("Copying Frontend Assets...")
    backend_static = os.path.join(os.getcwd(), "backend", "static_react")
    frontend_dist = os.path.join(frontend_dir, "dist")
    
    if not os.path.exists(frontend_dist):
        print(f"[X] Frontend build output not found at: {frontend_dist}")
        sys.exit(1)
        
    if os.path.exists(backend_static):
        shutil.rmtree(backend_static)
        
    shutil.copytree(frontend_dist, backend_static)
    print(f"[*] Assets copied to: {backend_static}")

    # 3. Setup Python Virtual Environment
    venv_dir = os.path.join(os.getcwd(), "venv")
    if not os.path.exists(venv_dir):
        print_step("Creating Python Virtual Environment...")
        venv.create(venv_dir, with_pip=True)
    else:
        print("[*] Using existing virtual environment.")

    # Determine Paths
    if os_type == "Windows":
        pip_cmd = os.path.join(venv_dir, "Scripts", "pip")
        pyinstaller_cmd = os.path.join(venv_dir, "Scripts", "pyinstaller")
        dist_ext = ".exe"
        sep = ";"
    else:
        pip_cmd = os.path.join(venv_dir, "bin", "pip")
        pyinstaller_cmd = os.path.join(venv_dir, "bin", "pyinstaller")
        dist_ext = ""
        sep = ":"

    # 4. Install Python Dependencies
    print_step("Installing Python Dependencies...")
    required_pkgs = ["pyserial", "pyinstaller", "flask", "flask-cors"]
    
    try:
        subprocess.check_call([pip_cmd, "install"] + required_pkgs)
    except subprocess.CalledProcessError:
        print("[X] Failed to install python dependencies.")
        sys.exit(1)

    # 5. Build Executable
    print_step("Building Executable...")
    
    # Clean previous builds
    for d in ["build", "dist"]:
        if os.path.exists(d):
            shutil.rmtree(d)
    
    # PyInstaller Arguments
    backend_dir = os.path.join(os.getcwd(), "backend")
    app_py = os.path.join(backend_dir, "app.py")
    add_data_arg = f"{backend_static}{sep}backend/static_react"
    
    build_cmd = [
        pyinstaller_cmd,
        "--onefile",
        "--name", "rf_config_app",
        "--add-data", add_data_arg,
        "--hidden-import", "binary_protocol",
        "--paths", backend_dir,
        app_py
    ]
    
    print(f"[*] Running: {' '.join(build_cmd)}")
    
    try:
        subprocess.check_call(build_cmd)
    except subprocess.CalledProcessError:
        print("[X] Build failed.")
        sys.exit(1)
        
    print_step("Build Complete!")
    output_bin = os.path.abspath(f"dist/rf_config_app{dist_ext}")
    
    if os.path.exists(output_bin):
        print(f"SUCCESS! Application created at:\n{output_bin}")
        print("\nRun this executable to start the Web Server and Browser.")
    else:
        print("[X] Build finished but output file not found.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Cancelled.")
        sys.exit(1)
