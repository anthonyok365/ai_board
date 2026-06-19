import { useState } from 'react';
import { Settings, RefreshCw, Copy, Check } from 'lucide-react';

export default function Sidebar({ config, onConfigChange }) {
  const [copied, setCopied] = useState(false);

  const handleChange = (key, value) => {
    onConfigChange({ ...config, [key]: value });
  };

  const generateNewThreadId = () => {
    const newId = `meeting_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    onConfigChange({ ...config, threadId: newId });
  };

  const copyThreadId = () => {
    navigator.clipboard.writeText(config.threadId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const providers = [
    { value: 'groq', label: 'Groq (Fast, Free)' },
    { value: 'gemini', label: 'Google Gemini' },
  ];

  const models = {
    groq: [
      { value: 'meta-llama/llama-4-scout-17b-16e-instruct', label: 'Llama 4 Scout (Fast)' },
    ],
    gemini: [
      { value: 'gemini-3.5-flash', label: 'Gemini 3.5 Flash (Most Capable)' },
    ],
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <Settings size={20} />
        <h2>Configuration</h2>
      </div>

      {/* LLM Provider */}
      <div className="config-section">
        <label>LLM Provider</label>
        <select
          value={config.provider}
          onChange={(e) => handleChange('provider', e.target.value)}
        >
          {providers.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
      </div>

      {/* Model */}
      <div className="config-section">
        <label>Model</label>
        <select
          value={config.model}
          onChange={(e) => handleChange('model', e.target.value)}
        >
          {models[config.provider]?.map((m) => (
            <option key={m.value} value={m.value}>
              {m.label}
            </option>
          ))}
        </select>
      </div>

      {/* Temperature */}
      <div className="config-section">
        <label>Temperature: {config.temperature}</label>
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={config.temperature}
          onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
        />
        <div className="temp-labels">
          <span>🎯 Focused</span>
          <span>💡 Creative</span>
        </div>
      </div>

      {/* Premium Toggle */}
      <div className="config-section">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={config.usePremium}
            onChange={(e) => handleChange('usePremium', e.target.checked)}
          />
          Use Premium Model
        </label>
      </div>

      {/* Thread ID */}
      <div className="config-section">
        <label>Session ID</label>
        <div className="thread-id-input">
          <input
            type="text"
            value={config.threadId}
            onChange={(e) => handleChange('threadId', e.target.value)}
            placeholder="Auto-generated"
          />
        </div>
        <div className="thread-id-buttons">
          <button onClick={generateNewThreadId} className="icon-btn" title="Generate New ID">
            <RefreshCw size={16} />
          </button>
          <button onClick={copyThreadId} className="icon-btn" title="Copy ID">
            {copied ? <Check size={16} /> : <Copy size={16} />}
          </button>
        </div>
      </div>

      {/* About */}
      <div className="about-section">
        <h3>ℹ️ About</h3>
        <p>AI Board of Directors v1.0</p>
        <p>Built with React & Vite</p>
      </div>
    </aside>
  );
}
