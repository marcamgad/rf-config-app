import { useState } from 'react'
import './index.css'

function App() {
    const [config, setConfig] = useState({
        deviceMode: 'receive',
        streamingProtocol: 'uart',
        modulation: 'QPSK',
        fc: 915000000,
        fs: 2000000,
        rfg: 14,
        ifg: 20,
        bbg: 30,
        rfg: 14,
        ifg: 20,
        bbg: 30,
        filePath: '',
        port: '' // Port for UART
    })

    const [status, setStatus] = useState(null)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [errors, setErrors] = useState({})

    // Validation ranges
    const ranges = {
        fc: { min: 1000000, max: 6000000000, label: '1 MHz - 6 GHz' },
        fs: { min: 1000000, max: 20000000, label: '1 MHz - 20 MHz' },
        rfg: { min: 0, max: 47, label: '0-47 dB' },
        ifg: { min: 0, max: 40, label: '0-40 dB' },
        bbg: { min: 0, max: 62, label: '0-62 dB' }
    }

    const validateField = (field, value) => {
        const range = ranges[field]
        if (!range) return true

        const numValue = parseFloat(value)
        if (isNaN(numValue)) return false

        return numValue >= range.min && numValue <= range.max
    }

    const validateAll = () => {
        const newErrors = {}

        Object.keys(ranges).forEach(field => {
            if (!validateField(field, config[field])) {
                newErrors[field] = `Must be between ${ranges[field].label}`
            }
        })

        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    const handleSubmit = async (e) => {
        e.preventDefault()

        if (!validateAll()) {
            setStatus({ type: 'error', message: 'Please fix validation errors before saving' })
            return
        }

        setIsSubmitting(true)
        setStatus(null)

        try {
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config)
            })

            if (response.ok) {
                const data = await response.json()
                setStatus({ type: 'success', message: `Configuration saved successfully! Files: ${data.bin_file}, ${data.txt_file}` })
            } else {
                const error = await response.json()
                setStatus({ type: 'error', message: error.error || 'Failed to save configuration' })
            }
        } catch (error) {
            setStatus({ type: 'error', message: 'Network error: ' + error.message })
        } finally {
            setIsSubmitting(false)
        }
    }

    const updateConfig = (field, value) => {
        setConfig(prev => ({ ...prev, [field]: value }))

        // Clear error for this field when user types
        if (errors[field]) {
            setErrors(prev => {
                const newErrors = { ...prev }
                delete newErrors[field]
                return newErrors
            })
        }
    }

    const handleFileSelect = (e) => {
        const file = e.target.files[0]
        if (file) {
            updateConfig('filePath', file.path || file.name)
        }
    }

    const handleCheckConnection = async () => {
        if (!config.port) {
            setStatus({ type: 'error', message: 'Please enter a Serial Port first' })
            return
        }
        setStatus({ type: 'info', message: 'Checking connection...' })
        try {
            const response = await fetch('/api/connection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ port: config.port })
            })
            const data = await response.json()
            if (response.ok) {
                setStatus({ type: 'success', message: data.message })
            } else {
                setStatus({ type: 'error', message: data.message || data.error })
            }
        } catch (error) {
            setStatus({ type: 'error', message: 'Network error: ' + error.message })
        }
    }

    const handleSendConfig = async () => {
        if (!config.port) {
            setStatus({ type: 'error', message: 'Please enter a Serial Port' })
            return
        }
        // Save first? check if isSubmitting

        setStatus({ type: 'info', message: 'Sending configuration...' })
        try {
            const response = await fetch('/api/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ port: config.port })
            })
            const data = await response.json()
            if (response.ok) {
                setStatus({ type: 'success', message: data.message })
            } else {
                setStatus({ type: 'error', message: data.message || data.error })
            }
        } catch (error) {
            setStatus({ type: 'error', message: 'Network error: ' + error.message })
        }
    }


    const hasErrors = Object.keys(errors).length > 0

    return (
        <div className="app-container">
            <header className="app-header">
                <h1 className="app-title">RF Configuration Tool</h1>
                <p className="app-subtitle">Configure HackRF One parameters for transmission and reception</p>
            </header>

            {status && (
                <div className={`status-message status-${status.type}`}>
                    {status.message}
                </div>
            )}

            <form onSubmit={handleSubmit}>
                {/* Device Mode Section */}
                <section className="config-section">
                    <h2 className="section-title">Device Configuration</h2>

                    <div className="form-group">
                        <label className="form-label">Device Mode</label>
                        <div className="radio-group">
                            <div className="radio-option">
                                <input
                                    type="radio"
                                    id="mode-receive"
                                    name="deviceMode"
                                    value="receive"
                                    checked={config.deviceMode === 'receive'}
                                    onChange={(e) => updateConfig('deviceMode', e.target.value)}
                                />
                                <label htmlFor="mode-receive" className="radio-label">Receive</label>
                            </div>
                            <div className="radio-option">
                                <input
                                    type="radio"
                                    id="mode-transmit"
                                    name="deviceMode"
                                    value="transmit"
                                    checked={config.deviceMode === 'transmit'}
                                    onChange={(e) => updateConfig('deviceMode', e.target.value)}
                                />
                                <label htmlFor="mode-transmit" className="radio-label">Transmit</label>
                            </div>
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label" htmlFor="protocol">Streaming Protocol</label>
                        <select
                            id="protocol"
                            className="form-select"
                            value={config.streamingProtocol}
                            onChange={(e) => updateConfig('streamingProtocol', e.target.value)}
                        >
                            <option value="uart">UART</option>
                            <option value="i2c">I2C</option>
                            <option value="spi">SPI</option>
                            <option value="file">File</option>
                        </select>
                    </div>

                    {config.streamingProtocol === 'file' && (
                        <div className="form-group">
                            <label className="form-label" htmlFor="file-input">Select File</label>
                            <input
                                type="file"
                                id="file-input"
                                className="form-input file-input"
                                onChange={handleFileSelect}
                                accept="*"
                            />
                            {config.filePath && (
                                <div className="form-hint success">Selected: {config.filePath}</div>
                            )}
                        </div>
                    )}
                </section>

                {/* RF Parameters Section */}
                <section className="config-section">
                    <h2 className="section-title">RF Parameters</h2>

                    <div className="form-group">
                        <label className="form-label" htmlFor="modulation">Modulation</label>
                        <select
                            id="modulation"
                            className="form-select"
                            value={config.modulation}
                            onChange={(e) => updateConfig('modulation', e.target.value)}
                        >
                            <option value="BPSK">BPSK</option>
                            <option value="QPSK">QPSK</option>
                            <option value="FSK">FSK</option>
                        </select>
                    </div>

                    <div className="form-grid">
                        <div className="form-group">
                            <label className="form-label" htmlFor="fc">Carrier Frequency (Hz)</label>
                            <input
                                type="number"
                                id="fc"
                                className={`form-input ${errors.fc ? 'error' : ''}`}
                                value={config.fc}
                                onChange={(e) => updateConfig('fc', e.target.value)}
                                onBlur={() => handleBlur('fc')}
                                step="1000000"
                            />
                            <div className={`form-hint ${errors.fc ? 'error' : ''}`}>
                                {errors.fc || `${(config.fc / 1e6).toFixed(3)} MHz (Range: ${ranges.fc.label})`}
                            </div>
                        </div>

                        <div className="form-group">
                            <label className="form-label" htmlFor="fs">Sampling Frequency (Hz)</label>
                            <input
                                type="number"
                                id="fs"
                                className={`form-input ${errors.fs ? 'error' : ''}`}
                                value={config.fs}
                                onChange={(e) => updateConfig('fs', e.target.value)}
                                onBlur={() => handleBlur('fs')}
                                step="100000"
                            />
                            <div className={`form-hint ${errors.fs ? 'error' : ''}`}>
                                {errors.fs || `${(config.fs / 1e6).toFixed(3)} MHz (Range: ${ranges.fs.label})`}
                            </div>
                        </div>
                    </div>
                </section>

                {/* Gain Controls Section */}
                <section className="config-section">
                    <h2 className="section-title">Gain Controls</h2>

                    <div className="form-grid">
                        <div className="form-group">
                            <label className="form-label" htmlFor="rfg">RF Gain (dB)</label>
                            <input
                                type="number"
                                id="rfg"
                                className={`form-input ${errors.rfg ? 'error' : ''}`}
                                value={config.rfg}
                                onChange={(e) => updateConfig('rfg', e.target.value)}
                                onBlur={() => handleBlur('rfg')}
                                step="1"
                            />
                            <div className={`form-hint ${errors.rfg ? 'error' : ''}`}>
                                {errors.rfg || `LNA Gain (Range: ${ranges.rfg.label})`}
                            </div>
                        </div>

                        <div className="form-group">
                            <label className="form-label" htmlFor="ifg">IF Gain (dB)</label>
                            <input
                                type="number"
                                id="ifg"
                                className={`form-input ${errors.ifg ? 'error' : ''}`}
                                value={config.ifg}
                                onChange={(e) => updateConfig('ifg', e.target.value)}
                                onBlur={() => handleBlur('ifg')}
                                step="1"
                            />
                            <div className={`form-hint ${errors.ifg ? 'error' : ''}`}>
                                {errors.ifg || `VGA Gain (Range: ${ranges.ifg.label})`}
                            </div>
                        </div>

                        <div className="form-group">
                            <label className="form-label" htmlFor="bbg">Baseband Gain (dB)</label>
                            <input
                                type="number"
                                id="bbg"
                                className={`form-input ${errors.bbg ? 'error' : ''}`}
                                value={config.bbg}
                                onChange={(e) => updateConfig('bbg', e.target.value)}
                                onBlur={() => handleBlur('bbg')}
                                step="1"
                            />
                            <div className={`form-hint ${errors.bbg ? 'error' : ''}`}>
                                {errors.bbg || `TX VGA Gain (Range: ${ranges.bbg.label})`}
                            </div>
                        </div>
                    </div>
                </section>

                {/* Current Configuration Display */}
                <section className="config-section">
                    <h2 className="section-title">Current Configuration</h2>
                    <div className="config-display">
                        <div className="config-item">
                            <span className="config-item-label">Device Mode</span>
                            <span className="config-item-value">{config.deviceMode.toUpperCase()}</span>
                        </div>
                        <div className="config-item">
                            <span className="config-item-label">Protocol</span>
                            <span className="config-item-value">{config.streamingProtocol.toUpperCase()}</span>
                        </div>
                        {config.streamingProtocol === 'file' && config.filePath && (
                            <div className="config-item">
                                <span className="config-item-label">File Path</span>
                                <span className="config-item-value">{config.filePath}</span>
                            </div>
                        )}
                        <div className="config-item">
                            <span className="config-item-label">Modulation</span>
                            <span className="config-item-value">{config.modulation}</span>
                        </div>
                        <div className="config-item">
                            <span className="config-item-label">Carrier Frequency</span>
                            <span className="config-item-value">{(config.fc / 1e6).toFixed(3)} MHz</span>
                        </div>
                        <div className="config-item">
                            <span className="config-item-label">Sampling Frequency</span>
                            <span className="config-item-value">{(config.fs / 1e6).toFixed(3)} MHz</span>
                        </div>
                        <div className="config-item">
                            <span className="config-item-label">RF Gain</span>
                            <span className="config-item-value">{config.rfg} dB</span>
                        </div>
                        <div className="config-item">
                            <span className="config-item-label">IF Gain</span>
                            <span className="config-item-value">{config.ifg} dB</span>
                        </div>
                        <div className="config-item">
                            <span className="config-item-label">Baseband Gain</span>
                            <span className="config-item-value">{config.bbg} dB</span>
                        </div>
                    </div>
                </section>

                {/* Action Buttons */}
                <div className="button-group">
                    <button
                        type="submit"
                        className="btn btn-primary"
                        disabled={isSubmitting || hasErrors}
                    >
                        {isSubmitting ? 'Saving...' : 'Save Configuration'}
                    </button>
                    <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={() => {
                            setConfig({
                                deviceMode: 'receive',
                                streamingProtocol: 'uart',
                                modulation: 'QPSK',
                                fc: 915000000,
                                fs: 2000000,
                                rfg: 14,
                                ifg: 20,
                                bbg: 30,
                                filePath: ''
                            })
                            setErrors({})
                        }}
                    >
                        Reset to Defaults
                    </button>
                </div>

                {/* Connection & Deployment Section */}
                <section className="config-section" style={{ marginTop: '20px', borderTop: '1px solid #eee', paddingTop: '20px' }}>
                    <h2 className="section-title">Device Connection</h2>
                    <div className="form-group">
                        <label className="form-label" htmlFor="port">Serial Port</label>
                        <div style={{ display: 'flex', gap: '10px' }}>
                            <input
                                type="text"
                                id="port"
                                className="form-input"
                                value={config.port}
                                onChange={(e) => updateConfig('port', e.target.value)}
                                placeholder="e.g. COM3 or /dev/ttyUSB0"
                                style={{ flex: 1 }}
                            />
                            <button
                                type="button"
                                className="btn btn-secondary"
                                onClick={handleCheckConnection}
                                disabled={!config.port}
                            >
                                Check Connection
                            </button>
                        </div>
                        <div className="form-hint">Connect your UART cable and enter the port name.</div>
                    </div>

                    <button
                        type="button"
                        className="btn btn-primary"
                        onClick={handleSendConfig}
                        disabled={!config.port}
                        style={{ width: '100%', marginTop: '10px', backgroundColor: '#28a745', borderColor: '#28a745' }}
                    >
                        Send to Device
                    </button>
                </section>
            </form>

        </div>
    )
}

export default App
