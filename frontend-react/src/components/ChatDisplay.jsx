import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import '../Chat.css';

const AGENT_CONFIG = {
  supervisor: { name: 'Board Chair', icon: '👔', color: '#6366F1', bgColor: '#EEF2FF' },
  strategist: { name: 'Chief Strategy Officer', icon: '🎯', color: '#3B82F6', bgColor: '#DBEAFE' },
  financial: { name: 'Chief Financial Officer', icon: '💰', color: '#10B981', bgColor: '#D1FAE5' },
  risk: { name: 'Chief Risk Officer', icon: '⚠️', color: '#F59E0B', bgColor: '#FEF3C7' },
  ceo: { name: 'Chief Executive Officer', icon: '👨‍💼', color: '#8B5CF6', bgColor: '#EDE9FE' },
  final_decision: { name: 'Board Secretary', icon: '📋', color: '#EC4899', bgColor: '#FCE7F3' },
  human: { name: 'You', icon: '👤', color: '#1F2937', bgColor: '#10B981' },
};

function getAgentInfo(name) {
  const key = (name || '').toLowerCase().trim();
  return AGENT_CONFIG[key] || { name: name || 'Board', icon: '🤖', color: '#6B7280', bgColor: '#F3F4F6' };
}

function isUserMessage(name) {
  return (name || '').toLowerCase().trim() === 'human';
}

export default function ChatDisplay({ messages }) {
  const [expandedCards, setExpandedCards] = useState({});

  if (!messages || messages.length === 0) {
    return (
      <div className="chat-placeholder">
        <div className="placeholder-icon">🏛️</div>
        <h3>No Meeting Yet</h3>
        <p>Enter a business question and start the board meeting</p>
      </div>
    );
  }

  const toggleExpand = (index) => {
    setExpandedCards(prev => ({ ...prev, [index]: !prev[index] }));
  };

  return (
    <div className="chat-container">
      {/* Header */}
      <div className="chat-header">
        <h3>💬 Board Discussion</h3>
        <span className="message-count">{messages.length} messages</span>
      </div>

      {/* Chat Messages */}
      <div className="chat-messages">
        {messages.map((msg, index) => {
          const info = getAgentInfo(msg.name);
          const content = msg.content || String(msg);
          const isUser = isUserMessage(msg.name);
          const isLong = content.length > 500;
          const isExpanded = expandedCards[index];
          const displayContent = isLong && !isExpanded ? content.substring(0, 400) + '...' : content;

          return (
            <div 
              key={index} 
              className={`chat-bubble-wrapper ${isUser ? 'user' : 'agent'}`}
            >
              {/* Avatar (only for agents on left) */}
              {!isUser && (
                <div className="avatar" style={{ backgroundColor: info.color }}>
                  {info.icon}
                </div>
              )}

              <div className="bubble-container">
                {/* Name Tag */}
                <div className={`name-tag ${isUser ? 'user-tag' : ''}`} style={{ color: info.color }}>
                  {info.name}
                </div>

                {/* Message Bubble */}
                <div 
                  className={`chat-bubble ${isUser ? 'user-bubble' : 'agent-bubble'}`}
                  style={isUser ? { backgroundColor: '#10B981' } : { backgroundColor: info.bgColor }}
                >
                  <div className="message-content">
                    <ReactMarkdown>{displayContent}</ReactMarkdown>
                  </div>
                  
                  {/* Expand/Collapse for long messages */}
                  {isLong && (
                    <button 
                      className="expand-btn"
                      onClick={() => toggleExpand(index)}
                      style={{ color: isUser ? '#fff' : info.color }}
                    >
                      {isExpanded ? 'Show less ↑' : 'Read more ↓'}
                    </button>
                  )}
                </div>

                {/* Timestamp */}
                <div className={`timestamp ${isUser ? 'user-time' : ''}`}>
                  Message {index + 1}
                </div>
              </div>

              {/* Avatar for user on right */}
              {isUser && (
                <div className="avatar user-avatar" style={{ backgroundColor: '#10B981' }}>
                  👤
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
