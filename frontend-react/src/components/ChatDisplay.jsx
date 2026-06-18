const AGENT_CONFIG = {
  supervisor: { name: 'Board Chair', icon: '👔', color: '#6366F1' },
  strategist: { name: 'Chief Strategy Officer', icon: '🎯', color: '#3B82F6' },
  financial: { name: 'Chief Financial Officer', icon: '💰', color: '#10B981' },
  risk: { name: 'Chief Risk Officer', icon: '⚠️', color: '#F59E0B' },
  ceo: { name: 'Chief Executive Officer', icon: '👨‍💼', color: '#8B5CF6' },
  final_decision: { name: 'Board Secretary', icon: '📋', color: '#EC4899' },
};

function getAgentInfo(name) {
  const key = (name || '').toLowerCase().trim();
  return AGENT_CONFIG[key] || { name: name || 'Unknown', icon: '🤖', color: '#6B7280' };
}

export default function ChatDisplay({ messages }) {
  if (!messages || messages.length === 0) {
    return (
      <div className="chat-placeholder">
        <div className="placeholder-icon">🏛️</div>
        <h3>No Meeting Yet</h3>
        <p>Enter a business question and start the board meeting</p>
      </div>
    );
  }

  // Group messages by agent
  const agentCounts = {};
  messages.forEach((msg) => {
    const name = msg.name || 'unknown';
    agentCounts[name] = (agentCounts[name] || 0) + 1;
  });

  return (
    <div className="chat-display">
      {/* Agent Summary */}
      <div className="agent-summary">
        {Object.entries(agentCounts).map(([name, count]) => {
          const info = getAgentInfo(name);
          return (
            <div key={name} className="agent-stat" style={{ borderColor: info.color }}>
              <span className="agent-icon">{info.icon}</span>
              <span className="agent-name">{info.name.split(' ').pop()}</span>
              <span className="agent-count">{count}</span>
            </div>
          );
        })}
      </div>

      {/* Messages */}
      <div className="messages-list">
        {messages.map((msg, index) => {
          const info = getAgentInfo(msg.name);
          const content = msg.content || msg;

          return (
            <div key={index} className="message-card" style={{ borderLeftColor: info.color }}>
              <div className="message-header">
                <div className="avatar" style={{ backgroundColor: info.color }}>
                  {info.icon}
                </div>
                <div className="message-meta">
                  <span className="agent-name">{info.name}</span>
                  <span className="agent-role">
                    {name === 'human' ? 'Human Input' : 'Board Member'}
                  </span>
                </div>
              </div>
              <div className="message-content">
                {content}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
