import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import '../Chat.css';

const AGENT_CONFIG = {
  supervisor: { name: 'Board Chair', icon: '👔', color: '#6366F1', bgColor: '#EEF2FF', textColor: '#1E40AF' },
  strategist: { name: 'Strategist', icon: '🎯', color: '#3B82F6', bgColor: '#DBEAFE', textColor: '#1E40AF' },
  financial: { name: 'Financial', icon: '💰', color: '#10B981', bgColor: '#D1FAE5', textColor: '#047857' },
  risk: { name: 'Risk Officer', icon: '⚠️', color: '#F59E0B', bgColor: '#FEF3C7', textColor: '#B45309' },
  ceo: { name: 'CEO', icon: '👨‍💼', color: '#8B5CF6', bgColor: '#EDE9FE', textColor: '#6D28D9' },
  final_decision: { name: 'Final Decision', icon: '📋', color: '#EC4899', bgColor: '#FCE7F3', textColor: '#BE185D' },
};

function getAgentInfo(name) {
  const key = (name || '').toLowerCase().trim();
  return AGENT_CONFIG[key] || { name: name || 'Board', icon: '🤖', color: '#6B7280', bgColor: '#F3F4F6', textColor: '#374151' };
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

  // Alternate messages: left, right, left, right...
  const isLeftSide = (index) => index % 2 === 0;

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
          const isLeft = isLeftSide(index);
          const isLong = content.length > 400;
          const isExpanded = expandedCards[index];
          const displayContent = isLong && !isExpanded ? content.substring(0, 350) + '...' : content;

          return (
            <div 
              key={index} 
              className={`chat-bubble-wrapper ${isLeft ? 'left' : 'right'}`}
            >
              {/* Avatar on the outer side */}
              <div className="avatar" style={{ backgroundColor: info.color }}>
                {info.icon}
              </div>

              <div className="bubble-container">
                {/* Name Tag */}
                <div className={`name-tag ${isLeft ? '' : 'right-align'}`} style={{ color: info.color }}>
                  {info.name}
                </div>

                {/* Message Bubble */}
                <div 
                  className={`chat-bubble ${isLeft ? 'bubble-left' : 'bubble-right'}`}
                  style={{ backgroundColor: info.bgColor }}
                >
                  <div className="message-content" style={{ color: info.textColor }}>
                    <ReactMarkdown>{displayContent}</ReactMarkdown>
                  </div>
                  
                  {/* Expand/Collapse for long messages */}
                  {isLong && (
                    <button 
                      className="expand-btn"
                      onClick={() => toggleExpand(index)}
                      style={{ color: info.color }}
                    >
                      {isExpanded ? 'Show less ↑' : 'Read more ↓'}
                    </button>
                  )}
                </div>

                {/* Message number indicator */}
                <div className={`timestamp ${isLeft ? '' : 'right-align'}`}>
                  #{index + 1}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
