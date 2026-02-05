import React from 'react';

function ConfigurationDisplay({ config, onReadConfig, onBack }) {
    const formatFrequency = (value) => {
        if (value >= 1e9) return `${(value / 1e9).toFixed(3)} GHz`;
        if (value >= 1e6) return `${(value / 1e6).toFixed(3)} MHz`;
        if (value >= 1e3) return `${(value / 1e3).toFixed(3)} kHz`;
        return `${value} Hz`;
    };

    return (
        <div className="slide-in">
            <div className="text-center mb-4">
                <div style={{ fontSize: '4rem', marginBottom: 'var(--spacing-md)' }}>
                    ✅
                </div>
                <h2>Configuration Complete!</h2>
                <p>Your device has been successfully configured</p>
            </div>

            <div style={{
                background: 'var(--color-bg-secondary)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--spacing-xl)',
                marginBottom: 'var(--spacing-xl)'
            }}>
                <h3 style={{ marginBottom: 'var(--spacing-lg)' }}>Configuration Summary</h3>

                <div style={{ display: 'grid', gap: 'var(--spacing-md)' }}>
                    <ConfigItem label="Device Mode" value={config.deviceMode} />
                    <ConfigItem label="Streaming Protocol" value={config.streamingProtocol?.toUpperCase()} />
                    <ConfigItem label="Modulation" value={config.modulation} />
                    <ConfigItem label="Carrier Frequency (fc)" value={formatFrequency(config.fc)} />
                    <ConfigItem label="Sampling Frequency (fs)" value={formatFrequency(config.fs)} />
                    <ConfigItem label="RF Gain (RFG)" value={`${config.rfg} dB`} />
                    <ConfigItem label="IF Gain (IfG)" value={`${config.ifg} dB`} />
                    <ConfigItem label="Baseband Gain (BBG)" value={`${config.bbg} dB`} />
                </div>
            </div>

            <div className="flex gap-3">
                <button className="btn btn-secondary" onClick={onBack}>
                    ← Back
                </button>
                <button className="btn btn-primary" onClick={onReadConfig} style={{ flex: 1 }}>
                    📖 Read Configuration
                </button>
            </div>
        </div>
    );
}

function ConfigItem({ label, value }) {
    return (
        <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: 'var(--spacing-sm) 0',
            borderBottom: '1px solid var(--color-border)'
        }}>
            <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
                {label}
            </span>
            <span style={{
                color: 'var(--color-accent-green)',
                fontWeight: 600,
                fontSize: '1rem'
            }}>
                {value}
            </span>
        </div>
    );
}

export default ConfigurationDisplay;
