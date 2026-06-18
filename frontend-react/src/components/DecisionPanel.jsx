import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

const SECTIONS = [
  { key: 'executive_summary', label: 'Executive Summary', icon: '📝', color: '#6366F1' },
  { key: 'key_recommendations', label: 'Key Recommendations', icon: '🎯', color: '#3B82F6' },
  { key: 'action_items', label: 'Action Items', icon: '✅', color: '#10B981' },
  { key: 'financial_impact', label: 'Financial Impact', icon: '💰', color: '#F59E0B' },
  { key: 'risks_mitigations', label: 'Risks & Mitigations', icon: '⚠️', color: '#EF4444' },
];

function parseDecision(decision) {
  if (!decision) return { raw: decision, sections: {} };

  const sections = {};
  const lines = decision.split('\n');
  let currentSection = 'raw';
  let currentContent = [];

  lines.forEach((line) => {
    const headerMatch = line.match(/^#+\s*(.+)/i);
    if (headerMatch) {
      const header = headerMatch[1].trim().toLowerCase().replace(/\s+/g, '_');
      if (sections[currentSection]) {
        sections[currentSection] += '\n' + currentContent.join('\n');
      } else {
        sections[currentSection] = currentContent.join('\n');
      }
      currentSection = header;
      currentContent = [];
    } else {
      currentContent.push(line);
    }
  });

  if (sections[currentSection]) {
    sections[currentSection] += '\n' + currentContent.join('\n');
  } else {
    sections[currentSection] = currentContent.join('\n');
  }

  return { raw: decision, sections };
}

export default function DecisionPanel({ decision }) {
  const [expandedSections, setExpandedSections] = useState(
    SECTIONS.reduce((acc, s) => ({ ...acc, [s.key]: true }), {})
  );

  const [showRaw, setShowRaw] = useState(false);

  const { sections } = parseDecision(decision);

  const toggleSection = (key) => {
    setExpandedSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  if (!decision) {
    return (
      <div className="decision-placeholder">
        <div className="placeholder-icon">📋</div>
        <h3>No Decision Yet</h3>
        <p>Complete a board meeting to see the decision</p>
      </div>
    );
  }

  return (
    <div className="decision-panel">
      <div className="decision-header">
        <h2>🎯 AI Board Decision</h2>
        <p>Official Position of the AI Board of Directors</p>
      </div>

      <div className="decision-sections">
        {SECTIONS.map((section) => {
          const content = sections[section.key];
          if (!content?.trim()) return null;

          return (
            <div key={section.key} className="section-card" style={{ borderColor: section.color }}>
              <button
                className="section-header"
                onClick={() => toggleSection(section.key)}
                style={{ borderBottomColor: expandedSections[section.key] ? section.color : 'transparent' }}
              >
                <div className="section-title">
                  <span className="section-icon">{section.icon}</span>
                  <span>{section.label}</span>
                </div>
                {expandedSections[section.key] ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
              </button>
              {expandedSections[section.key] && (
                <div className="section-content">
                  <pre>{content.trim()}</pre>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <button className="raw-toggle" onClick={() => setShowRaw(!showRaw)}>
        {showRaw ? 'Hide' : 'Show'} Raw Decision
      </button>
      {showRaw && (
        <div className="raw-decision">
          <pre>{decision}</pre>
        </div>
      )}
    </div>
  );
}
