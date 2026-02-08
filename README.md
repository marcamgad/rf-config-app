# RF Config App

A cross-platform desktop application for configuring RF devices (HackRF One) via UART. Built with React and Flask, packaged as a single standalone executable.

## Quick Start

### For End Users

1. **Clone or Download**
   ```bash
   git clone https://github.com/marcamgad/rf-config-app.git
   cd rf-config-app
   ```

2. **Run the Installer**
   
   **Windows**: Double-click `install_windows.bat`
   
   **Linux**: 
   ```bash
   chmod +x install_linux.sh
   ./install_linux.sh
   ```

3. **Run the Application**
   
   **Windows**: `dist\rf_config_app.exe`
   
   **Linux**: `./dist/rf_config_app`

4. **Use the App**
   - Browser opens automatically
   - Configure RF parameters in the web interface
   - Enter your serial port (e.g., `COM3` or `/dev/ttyUSB0`)
   - Click "Check Connection" to verify
   - Click "Send to Device" to transmit configuration

## Features

- **Web-Based UI**: Modern React interface served locally
- **UART Communication**: Direct device configuration via serial port
- **Connection Testing**: Verify port connectivity before sending
- **Binary Protocol**: Efficient CRC-protected configuration format
- **Cross-Platform**: Works on Windows and Linux
- **Zero Dependencies**: Standalone executable - no Python or Node.js needed to run

## Configuration Parameters

- **Device Mode**: Transmit/Receive
- **Streaming Protocol**: UART/I2C/SPI/File
- **Modulation**: BPSK/QPSK/FSK
- **Carrier Frequency**: 1 MHz - 6 GHz
- **Sampling Frequency**: 1 MHz - 20 MHz
- **Gain Controls**: RF (0-47 dB), IF (0-40 dB), Baseband (0-62 dB)

## Project Structure

```
rf-config-app/
├── README.md                 # This file
├── install.py                # Universal build script
├── install_windows.bat       # Windows installer
├── install_linux.sh          # Linux installer
├── backend/                  # Flask backend
│   ├── app.py
│   ├── binary_protocol.py
│   └── uart_sender.py
├── frontend/                 # React frontend
│   ├── src/
│   └── package.json
└── dist/                     # Built executable (after install)
    └── rf_config_app
```

## Development

### Prerequisites
- Python 3.6+
- Node.js and npm

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install flask flask-cors pyserial
python app.py
```

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
