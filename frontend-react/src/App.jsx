import { useState } from 'react';
import { Play, Trash2, Download, RotateCcw, AlertCircle } from 'lucide-react';
import { useMeeting } from './hooks/useMeeting';
import Sidebar from './components/Sidebar';
import ChatDisplay from './components/ChatDisplay';
import DecisionPanel from './components/DecisionPanel';
import './App.css';

const defaultConfig = {
  provider: 'groq',
  model: 'meta-llama/llama-4-scout-17b-16e-instruct',
  temperature: 0.7,
  usePremium: false,
  threadId: `meeting_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
};

function App() {
  const [query, setQuery] = useState('');
  const [config, setConfig] = useState(defaultConfig);
  const [debugInfo, setDebugInfo] = useState(null);
  
  const {
    loading,
    error,
    result,
    threadId,
    startMeeting,
    reset,
  } = useMeeting();

  const handleStartMeeting = async () => {
    if (!query.trim()) return;
    
    setDebugInfo(null);
    
    try {
      await startMeeting({
        query: query.trim(),
        provider: config.provider,
        usePremium: config.usePremium,
      });
    } catch (err) {
      setDebugInfo({
        message: err.message,
        response: err.response?.data,
        backendUrl: import.meta.env.VITE_API_URL || 'https://ai-board-backend-production.up.railway.app',
      });
    }
  };

  const handleClear = () => {
    setQuery('');
    setDebugInfo(null);
    reset();
  };

  const handleExport = () => {
    if (!result) return;
    
    const data = {
      thread_id: result.thread_id,
      query: result.query,
      status: result.status,
      result: result.result,
      messages: result.messages,
      timestamp: new Date().toISOString(),
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${result.thread_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleNewMeeting = () => {
    setQuery('');
    setDebugInfo(null);
    reset();
    setConfig({
      ...defaultConfig,
      threadId: `meeting_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    });
  };

  const messages = result?.messages || result?.result?.messages || [];

  return (
    <div className="app">
      <Sidebar config={config} onConfigChange={setConfig} />
      
      <main className="main-content">
        {/* Header */}
        <header className="header">
          <h1>🏢 AI Board of Directors</h1>
          <p>Multi-Agent Business Decision Making</p>
        </header>

        {/* Query Input */}
        <section className="query-section">
          <h3>📋 Business Question</h3>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Example: Should we invest $800k in expanding our AI product line next quarter?"
            rows={4}
            disabled={loading}
          />
          
          <div className="button-row">
            <button
              className="btn-primary"
              onClick={handleStartMeeting}
              disabled={loading || !query.trim()}
            >
              <Play size={20} />
              {loading ? 'Running Meeting...' : 'Start Board Meeting'}
            </button>
            
            <button className="btn-secondary" onClick={handleClear} disabled={loading}>
              <Trash2 size={18} />
              Clear
            </button>
          </div>
        </section>

        {/* Loading State */}
        {loading && (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Board members are deliberating...</p>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="error-display">
            <div className="error-header">
              <AlertCircle size={24} />
              <h3>Error Running Meeting</h3>
            </div>
            
            <details className="error-details">
              <summary>View Error Details</summary>
              <div className="error-content">
                <p><strong>Message:</strong> {error}</p>
                {debugInfo && (
                  <>
                    <p><strong>Backend URL:</strong> {debugInfo.backendUrl}</p>
                    {debugInfo.response && (
                      <p><strong>Server Response:</strong></p>
                    )}
                  </>
                )}
              </div>
            </details>
          </div>
        )}

        {/* Success Message */}
        {result && !loading && !error && (
          <div className="success-display">
            🎉 Meeting completed! Thread ID: {result.thread_id}
          </div>
        )}

        {/* Chat Display */}
        {messages.length > 0 && (
          <section className="chat-section">
            <ChatDisplay messages={messages} />
          </section>
        )}

        {/* Decision Panel */}
        {result?.result?.decision && (
          <section className="decision-section">
            <DecisionPanel decision={result.result.decision} />
          </section>
        )}

        {/* Action Buttons */}
        {result && !loading && (
          <section className="actions-section">
            <button className="btn-action" onClick={handleExport}>
              <Download size={18} />
              Export JSON
            </button>
            <button className="btn-action" onClick={handleNewMeeting}>
              <RotateCcw size={18} />
              New Meeting
            </button>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
