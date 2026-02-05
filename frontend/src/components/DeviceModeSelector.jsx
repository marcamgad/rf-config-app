import React from 'react';

function DeviceModeSelector({ selectedMode, onSelect }) {
    const modes = [
        {
            id: 'receive',
            title: 'Receive',
            description: 'Configure device to receive RF signals',
            icon: '📡'
        },
        {
            id: 'transmit',
            title: 'Transmit',
            description: 'Configure device to transmit RF signals',
            icon: '📤'
        }
    ];

    return (
        <div className="slide-in">
            <h2>Select Device Mode</h2>
            <p>Choose whether your device will receive or transmit RF signals</p>

            <div className="option-group">
                {modes.map((mode) => (
                    <div
                        key={mode.id}
                        className={`option-card ${selectedMode === mode.id ? 'active' : ''}`}
                        onClick={() => onSelect(mode.id)}
                    >
                        <div style={{ fontSize: '3rem', marginBottom: 'var(--spacing-sm)' }}>
                            {mode.icon}
                        </div>
                        <div className="option-title">{mode.title}</div>
                        <p className="option-description">{mode.description}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default DeviceModeSelector;
