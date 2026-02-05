import React, { useState } from 'react';

function RFConfiguration({ onSubmit, onBack }) {
    const [formData, setFormData] = useState({
        modulation: 'QPSK',
        fc: '',
        fs: '',
        rfg: '',
        ifg: '',
        bbg: ''
    });

    const [errors, setErrors] = useState({});
    const [touched, setTouched] = useState({});

    // Validation ranges (these can be adjusted based on actual hardware specs)
    const validationRules = {
        fc: { min: 1e6, max: 6e9, unit: 'Hz', label: 'Carrier Frequency', hint: 'Range: 1 MHz - 6 GHz' },
        fs: { min: 1e6, max: 20e6, unit: 'Hz', label: 'Sampling Frequency', hint: 'Range: 1 MHz - 20 MHz' },
        rfg: { min: 0, max: 47, unit: 'dB', label: 'RF Gain', hint: 'Range: 0 - 47 dB' },
        ifg: { min: 0, max: 40, unit: 'dB', label: 'IF Gain', hint: 'Range: 0 - 40 dB' },
        bbg: { min: 0, max: 62, unit: 'dB', label: 'Baseband Gain', hint: 'Range: 0 - 62 dB' }
    };

    const validateField = (name, value) => {
        if (!value) {
            return 'This field is required';
        }

        const numValue = parseFloat(value);
        if (isNaN(numValue)) {
            return 'Must be a valid number';
        }

        const rule = validationRules[name];
        if (rule) {
            if (numValue < rule.min) {
                return `Value too low. Minimum: ${formatValue(rule.min, rule.unit)}`;
            }
            if (numValue > rule.max) {
                return `Value too high. Maximum: ${formatValue(rule.max, rule.unit)}`;
            }
        }

        return null;
    };

    const formatValue = (value, unit) => {
        if (unit === 'Hz') {
            if (value >= 1e9) return `${value / 1e9} GHz`;
            if (value >= 1e6) return `${value / 1e6} MHz`;
            if (value >= 1e3) return `${value / 1e3} kHz`;
            return `${value} Hz`;
        }
        return `${value} ${unit}`;
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));

        // Validate on change if field has been touched
        if (touched[name]) {
            const error = validateField(name, value);
            setErrors(prev => ({ ...prev, [name]: error }));
        }
    };

    const handleBlur = (e) => {
        const { name, value } = e.target;
        setTouched(prev => ({ ...prev, [name]: true }));
        const error = validateField(name, value);
        setErrors(prev => ({ ...prev, [name]: error }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();

        // Validate all fields
        const newErrors = {};
        Object.keys(validationRules).forEach(field => {
            const error = validateField(field, formData[field]);
            if (error) newErrors[field] = error;
        });

        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors);
            setTouched({
                fc: true,
                fs: true,
                rfg: true,
                ifg: true,
                bbg: true
            });
            return;
        }

        // Submit configuration
        onSubmit({
            modulation: formData.modulation,
            fc: parseFloat(formData.fc),
            fs: parseFloat(formData.fs),
            rfg: parseFloat(formData.rfg),
            ifg: parseFloat(formData.ifg),
            bbg: parseFloat(formData.bbg)
        });
    };

    const getInputClassName = (fieldName) => {
        if (!touched[fieldName]) return 'input-field';
        return `input-field ${errors[fieldName] ? 'error' : 'success'}`;
    };

    const modulations = ['QPSK', 'BPSK', 'FSK'];

    return (
        <div className="slide-in">
            <h2>RF Configuration</h2>
            <p>Configure the RF parameters for your device</p>

            <form onSubmit={handleSubmit}>
                {/* Modulation Selection */}
                <div className="input-group">
                    <label className="input-label">Modulation Scheme</label>
                    <div className="option-group" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
                        {modulations.map((mod) => (
                            <div
                                key={mod}
                                className={`option-card ${formData.modulation === mod ? 'active' : ''}`}
                                onClick={() => setFormData(prev => ({ ...prev, modulation: mod }))}
                                style={{ padding: 'var(--spacing-md)' }}
                            >
                                <div className="option-title" style={{ fontSize: '1rem', marginBottom: 0 }}>
                                    {mod}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Frequency Configuration */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-lg)' }}>
                    <div className="input-group">
                        <label className="input-label" htmlFor="fc">
                            {validationRules.fc.label} (fc)
                        </label>
                        <input
                            type="text"
                            id="fc"
                            name="fc"
                            className={getInputClassName('fc')}
                            value={formData.fc}
                            onChange={handleChange}
                            onBlur={handleBlur}
                            placeholder="e.g., 915000000 (915 MHz)"
                        />
                        <div className={`input-hint ${errors.fc ? 'error' : touched.fc && !errors.fc ? 'success' : ''}`}>
                            {errors.fc || validationRules.fc.hint}
                        </div>
                    </div>

                    <div className="input-group">
                        <label className="input-label" htmlFor="fs">
                            {validationRules.fs.label} (fs)
                        </label>
                        <input
                            type="text"
                            id="fs"
                            name="fs"
                            className={getInputClassName('fs')}
                            value={formData.fs}
                            onChange={handleChange}
                            onBlur={handleBlur}
                            placeholder="e.g., 2000000 (2 MHz)"
                        />
                        <div className={`input-hint ${errors.fs ? 'error' : touched.fs && !errors.fs ? 'success' : ''}`}>
                            {errors.fs || validationRules.fs.hint}
                        </div>
                    </div>
                </div>

                {/* Gain Configuration */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--spacing-lg)' }}>
                    <div className="input-group">
                        <label className="input-label" htmlFor="rfg">
                            {validationRules.rfg.label} (RFG)
                        </label>
                        <input
                            type="text"
                            id="rfg"
                            name="rfg"
                            className={getInputClassName('rfg')}
                            value={formData.rfg}
                            onChange={handleChange}
                            onBlur={handleBlur}
                            placeholder="e.g., 14"
                        />
                        <div className={`input-hint ${errors.rfg ? 'error' : touched.rfg && !errors.rfg ? 'success' : ''}`}>
                            {errors.rfg || validationRules.rfg.hint}
                        </div>
                    </div>

                    <div className="input-group">
                        <label className="input-label" htmlFor="ifg">
                            {validationRules.ifg.label} (IfG)
                        </label>
                        <input
                            type="text"
                            id="ifg"
                            name="ifg"
                            className={getInputClassName('ifg')}
                            value={formData.ifg}
                            onChange={handleChange}
                            onBlur={handleBlur}
                            placeholder="e.g., 20"
                        />
                        <div className={`input-hint ${errors.ifg ? 'error' : touched.ifg && !errors.ifg ? 'success' : ''}`}>
                            {errors.ifg || validationRules.ifg.hint}
                        </div>
                    </div>

                    <div className="input-group">
                        <label className="input-label" htmlFor="bbg">
                            {validationRules.bbg.label} (BBG)
                        </label>
                        <input
                            type="text"
                            id="bbg"
                            name="bbg"
                            className={getInputClassName('bbg')}
                            value={formData.bbg}
                            onChange={handleChange}
                            onBlur={handleBlur}
                            placeholder="e.g., 30"
                        />
                        <div className={`input-hint ${errors.bbg ? 'error' : touched.bbg && !errors.bbg ? 'success' : ''}`}>
                            {errors.bbg || validationRules.bbg.hint}
                        </div>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 mt-5">
                    <button type="button" className="btn btn-secondary" onClick={onBack}>
                        ← Back
                    </button>
                    <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                        Configure Device
                    </button>
                </div>
            </form>
        </div>
    );
}

export default RFConfiguration;
