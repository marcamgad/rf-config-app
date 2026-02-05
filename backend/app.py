from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Store the current configuration
current_config = None

# Directory to store configuration files
CONFIG_DIR = os.path.join(os.path.dirname(__file__), 'config_files')
os.makedirs(CONFIG_DIR, exist_ok=True)

# Directory for React Static Files (bundled)
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static_react')

@app.route('/')
def serve_react_app():
    """
    Serve the React application (index.html).
    """
    if os.path.exists(os.path.join(STATIC_DIR, 'index.html')):
        return send_file(os.path.join(STATIC_DIR, 'index.html'))
    else:
        return "React Frontend not found. Please build the application first.", 404

@app.route('/<path:path>')
def serve_static_files(path):
    """
    Serve static files (js, css, etc.) or fallback to index.html for React Router.
    """
    # Check if file exists in static folder
    if os.path.exists(os.path.join(STATIC_DIR, path)):
        return send_file(os.path.join(STATIC_DIR, path))
    
    # Fallback to index.html for React Router paths (e.g. /about) (unless it's an API call)
    if not path.startswith('api/') and os.path.exists(os.path.join(STATIC_DIR, 'index.html')):
        return send_file(os.path.join(STATIC_DIR, 'index.html'))
        
    return "File not found", 404


def generate_config_file(config):
    """
    Generate configuration files for the single board computer.
    Creates both a binary file and a compact string.
    """
    from binary_protocol import encode_config_binary, decode_config_binary, format_binary_hex
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate binary configuration
    binary_data = encode_config_binary(config)
    
    # Save binary configuration file
    bin_filename = f"rf_config_{timestamp}.bin"
    bin_filepath = os.path.join(CONFIG_DIR, bin_filename)
    with open(bin_filepath, 'wb') as f:
        f.write(binary_data)
    
    # Decode for verification and response
    decoded_config = decode_config_binary(binary_data)
    
    # Create a structured configuration dictionary for response
    sbc_config = {
        "timestamp": timestamp,
        "device_mode": config.get('deviceMode', 'receive'),
        "streaming_protocol": config.get('streamingProtocol', 'uart'),
        "rf_parameters": {
            "modulation": config.get('modulation', 'QPSK'),
            "carrier_frequency_hz": int(config.get('fc', 0)),
            "sampling_frequency_hz": int(config.get('fs', 0)),
            "rf_gain_db": float(config.get('rfg', 0)),
            "if_gain_db": float(config.get('ifg', 0)),
            "baseband_gain_db": float(config.get('bbg', 0))
        },
        "binary_info": {
            "size_bytes": len(binary_data),
            "crc": decoded_config['crc'],
            "hex_preview": format_binary_hex(binary_data, bytes_per_line=16)
        }
    }
    
    # Generate a compact string format for serial transmission
    # Format: MODE|PROTOCOL|MOD|FC|FS|RFG|IFG|BBG
    compact_string = (
        f"{sbc_config['device_mode'].upper()}|"
        f"{sbc_config['streaming_protocol'].upper()}|"
        f"{sbc_config['rf_parameters']['modulation']}|"
        f"{sbc_config['rf_parameters']['carrier_frequency_hz']}|"
        f"{sbc_config['rf_parameters']['sampling_frequency_hz']}|"
        f"{sbc_config['rf_parameters']['rf_gain_db']}|"
        f"{sbc_config['rf_parameters']['if_gain_db']}|"
        f"{sbc_config['rf_parameters']['baseband_gain_db']}"
    )
    
    # Save compact string to text file
    txt_filename = f"rf_config_{timestamp}.txt"
    txt_filepath = os.path.join(CONFIG_DIR, txt_filename)
    with open(txt_filepath, 'w') as f:
        f.write(compact_string)
    
    return {
        'bin_file': bin_filepath,
        'txt_file': txt_filepath,
        'compact_string': compact_string,
        'config': sbc_config
    }


@app.route('/api/config', methods=['POST'])
def set_configuration():
    """
    Receive configuration from frontend and generate config files.
    """
    global current_config
    
    try:
        config_data = request.json
        
        # Validate required fields
        required_fields = ['deviceMode', 'streamingProtocol', 'modulation', 'fc', 'fs', 'rfg', 'ifg', 'bbg']
        for field in required_fields:
            if field not in config_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate ranges
        validation_errors = []
        
        fc = float(config_data['fc'])
        if fc < 1e6 or fc > 6e9:
            validation_errors.append('Carrier frequency must be between 1 MHz and 6 GHz')
        
        fs = float(config_data['fs'])
        if fs < 1e6 or fs > 20e6:
            validation_errors.append('Sampling frequency must be between 1 MHz and 20 MHz')
        
        rfg = float(config_data['rfg'])
        if rfg < 0 or rfg > 47:
            validation_errors.append('RF Gain must be between 0 and 47 dB')
        
        ifg = float(config_data['ifg'])
        if ifg < 0 or ifg > 40:
            validation_errors.append('IF Gain must be between 0 and 40 dB')
        
        bbg = float(config_data['bbg'])
        if bbg < 0 or bbg > 62:
            validation_errors.append('Baseband Gain must be between 0 and 62 dB')
        
        if validation_errors:
            return jsonify({'error': 'Validation failed', 'details': validation_errors}), 400
        
        # Generate configuration files
        result = generate_config_file(config_data)
        
        # Store current configuration
        current_config = result['config']
        
        # Return response with file paths and compact string
        return jsonify({
            'status': 'success',
            'message': 'Configuration saved successfully',
            'bin_file': os.path.basename(result['bin_file']),
            'txt_file': os.path.basename(result['txt_file']),
            'compact_string': result['compact_string'],
            **current_config
        }), 200
        
    except ValueError as e:
        return jsonify({'error': f'Invalid value: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/config', methods=['GET'])
def get_configuration():
    """
    Read the current configuration.
    """
    if current_config is None:
        return jsonify({'error': 'No configuration set'}), 404
    
    return jsonify(current_config), 200


@app.route('/api/config/download/<filename>', methods=['GET'])
def download_config_file(filename):
    """
    Download a specific configuration file.
    """
    filepath = os.path.join(CONFIG_DIR, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(filepath, as_attachment=True)


@app.route('/api/config/files', methods=['GET'])
def list_config_files():
    """
    List all generated configuration files.
    """
    files = []
    for filename in os.listdir(CONFIG_DIR):
        filepath = os.path.join(CONFIG_DIR, filename)
        files.append({
            'filename': filename,
            'size': os.path.getsize(filepath),
            'created': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
        })
    
    return jsonify({'files': files}), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    """
    return jsonify({'status': 'healthy', 'service': 'RF Configuration Backend'}), 200


@app.route('/api/connection', methods=['POST'])
def check_uart_connection():
    """
    Check if the UART connection is valid.
    """
    data = request.json
    port = data.get('port')
    baudrate = int(data.get('baudrate', 115200))
    
    if not port:
        return jsonify({'error': 'Port is required'}), 400
        
    try:
        # Import dynamically to avoid circular issues or if file missing
        from uart_sender import check_connection
        success = check_connection(port, baudrate)
        
        if success:
            return jsonify({'status': 'connected', 'message': f'Successfully connected to {port}'}), 200
        else:
            return jsonify({'status': 'failed', 'message': f'Could not open {port}'}), 400
            
    except ImportError:
        return jsonify({'error': 'uart_sender module not found'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/send', methods=['POST'])
def send_configuration():
    """
    Send the current or provided configuration via UART.
    """
    data = request.json
    port = data.get('port')
    baudrate = int(data.get('baudrate', 115200))
    
    if not port:
        return jsonify({'error': 'Port is required'}), 400

    # We can either use the provided config or the last saved one.
    # For safety, let's require the config to be generated/saved first.
    # However, to be user friendly, we can use the 'last generated' file if available.
    if current_config is None:
        return jsonify({'error': 'No configuration generated yes. Please save configuration first.'}), 400
        
    # Find the latest generated .bin file
    try:
        files = sorted(
            [f for f in os.listdir(CONFIG_DIR) if f.endswith('.bin')],
            key=lambda x: os.path.getctime(os.path.join(CONFIG_DIR, x)),
            reverse=True
        )
        
        if not files:
            return jsonify({'error': 'No binary config files found'}), 404
            
        latest_bin = os.path.join(CONFIG_DIR, files[0])
        
        from uart_sender import send_config_uart
        
        # Determine if we function as library or separate process
        # Using library call:
        # Note: send_config_uart currently prints to stdout. 
        # We might want to capture that or trust it returns True/False.
        success = send_config_uart(port, baudrate, latest_bin)
        
        if success:
            return jsonify({'status': 'success', 'message': 'Configuration sent successfully!'}), 200
        else:
            return jsonify({'status': 'failed', 'message': 'Failed to send configuration. Check connection.'}), 500
            
    except ImportError:
        return jsonify({'error': 'uart_sender module not found'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':

    print("=" * 60)
    print("RF Configuration Backend Server")
    print("=" * 60)
    print("Server running on: http://localhost:5000")
    print("API Endpoints:")
    print("  POST   /api/config          - Submit configuration")
    print("  GET    /api/config          - Read current configuration")
    print("  GET    /api/config/files    - List all config files")
    print("  GET    /api/config/download/<filename> - Download config file")
    print("  GET    /api/health          - Health check")
    print("=" * 60)
    print(f"Configuration files will be saved to: {CONFIG_DIR}")
    print("=" * 60)
    
    import webbrowser
    from threading import Timer

    def open_browser():
        webbrowser.open_new('http://localhost:5000')

    # Schedule browser opening
    Timer(1.5, open_browser).start()
    
    app.run(debug=False, host='0.0.0.0', port=5000)

