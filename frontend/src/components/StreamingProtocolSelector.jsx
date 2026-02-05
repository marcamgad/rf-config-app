import React, { useState } from 'react';

function StreamingProtocolSelector({ selectedProtocol, onSelect, onBack }) {
    const [selectedFile, setSelectedFile] = useState(null);

    const protocols = [
        {
            id: 'uart',
            title: 'UART',
            description: 'Universal Asynchronous Receiver-Transmitter',
            icon: '🔌'
        },
        {
            id: 'i2c',
            title: 'I2C',
            description: 'Inter-Integrated Circuit',
            icon: '🔗'
        },
        {
            id: 'spi',
            title: 'SPI',
            description: 'Serial Peripheral Interface',
            icon: '⚡'
        },
        {
            id: 'file',
            title: 'File',
            description: 'Load from file',
            icon: '📁'
        }
    ];

    const handleProtocolSelect = (protocolId) => {
        if (protocolId === 'file') {
            // Don't proceed immediately, wait for file selection
            return;
        }
        onSelect(protocolId);
    };

    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (file) {
            setSelectedFile(file);
            onSelect('file', file);
        }
    };

    return (
        <div className="slide-in">
            <h2>Select Streaming Protocol</h2>
            <p>Choose the communication protocol for data streaming</p>

            <div className="option-group">
                {protocols.map((protocol) => (
                    <div
                        key={protocol.id}
                        className={`option-card ${selectedProtocol === protocol.id ? 'active' : ''}`}
                        onClick={() => handleProtocolSelect(protocol.id)}
                    >
                        <div style={{ fontSize: '3rem', marginBottom: 'var(--spacing-sm)' }}>
                            {protocol.icon}
                        </div>
                        <div className="option-title">{protocol.title}</div>
                        <p className="option-description">{protocol.description}</p>
                    </div>
                ))}
            </div>

            {selectedProtocol === 'file' && (
                <div className="file-browser fade-in">
                    <input
                        type="file"
                        id="file-input"
                        onChange={handleFileChange}
                        accept=".bin,.dat,.txt"
                    />
                    <label htmlFor="file-input">
                        <div style={{ fontSize: '2rem', marginBottom: 'var(--spacing-sm)' }}>
                            📂
                        </div>
                        <div style={{ color: 'var(--color-text-primary)', fontWeight: 500 }}>
                            {selectedFile ? selectedFile.name : 'Click to browse files'}
                        </div>
                        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginTop: 'var(--spacing-xs)' }}>
                            Supported formats: .bin, .dat, .txt
                        </p>
                    </label>
                </div>
            )}

            <div className="flex gap-3 mt-4">
                <button className="btn btn-secondary" onClick={onBack}>
                    ← Back
                </button>
            </div>
        </div>
    );
}

export default StreamingProtocolSelector;
