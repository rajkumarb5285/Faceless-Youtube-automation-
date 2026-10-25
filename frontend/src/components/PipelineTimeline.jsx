import React from 'react';
import { 
  Compass, Search, CheckCircle2, ListOrdered, FileText, 
  Scale, UserCheck, Film, Mic, Video, ShieldCheck, 
  Tag, Send, BarChart2 
} from 'lucide-react';

const NODE_CONFIG = [
  { id: 'strategist', label: '1. Strategist', icon: Compass },
  { id: 'researcher', label: '2. Researcher', icon: Search },
  { id: 'verifier', label: '3. Verifier', icon: CheckCircle2 },
  { id: 'planner', label: '4. Planner', icon: ListOrdered },
  { id: 'scriptwriter', label: '5. Scriptwriter', icon: FileText },
  { id: 'critic', label: '6. Critic Gate', icon: Scale },
  { id: 'human_review', label: '7. Human Gate', icon: UserCheck },
  { id: 'visuals', label: '8. Visual Planner', icon: Film },
  { id: 'voice', label: '9. Voice Director', icon: Mic },
  { id: 'render', label: '10. FFmpeg Render', icon: Video },
  { id: 'qa_gate', label: '11. QA Gate', icon: ShieldCheck },
  { id: 'metadata', label: '12. Metadata', icon: Tag },
  { id: 'publish', label: '13. Publisher', icon: Send },
  { id: 'analyst', label: '14. Analyst', icon: BarChart2 }
];

export default function PipelineTimeline({ currentStep, waitingGate, status }) {
  const currentIndex = NODE_CONFIG.findIndex(n => n.id === currentStep);

  return (
    <div className="glass-panel" style={{ padding: '20px 24px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-muted)' }}>
          LANGGRAPH STATE MACHINE PIPELINE (14 STAGES)
        </h3>
        {status && (
          <span style={{ 
            fontSize: '12px', 
            fontWeight: '600', 
            padding: '4px 10px', 
            borderRadius: '12px',
            textTransform: 'uppercase',
            background: status === 'completed' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(59, 130, 246, 0.15)',
            color: status === 'completed' ? '#34D399' : '#60A5FA'
          }}>
            Status: {status}
          </span>
        )}
      </div>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', 
        gap: '10px' 
      }}>
        {NODE_CONFIG.map((node, idx) => {
          const Icon = node.icon;
          const isCurrent = node.id === currentStep;
          const isDone = currentIndex > idx || status === 'completed';
          const isWaiting = isCurrent && waitingGate;

          let badgeBg = 'rgba(255, 255, 255, 0.03)';
          let borderColor = 'var(--border)';
          let iconColor = 'var(--text-muted)';
          let textColor = 'var(--text-muted)';

          if (isDone) {
            badgeBg = 'rgba(16, 185, 129, 0.08)';
            borderColor = 'rgba(16, 185, 129, 0.3)';
            iconColor = '#34D399';
            textColor = '#F8FAFC';
          }
          if (isCurrent) {
            badgeBg = 'rgba(59, 130, 246, 0.15)';
            borderColor = '#3B82F6';
            iconColor = '#60A5FA';
            textColor = '#FFFFFF';
          }
          if (isWaiting) {
            badgeBg = 'rgba(245, 158, 11, 0.18)';
            borderColor = '#F59E0B';
            iconColor = '#FBBF24';
          }

          return (
            <div 
              key={node.id}
              className={isCurrent ? "node-active" : ""}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 12px',
                borderRadius: '10px',
                background: badgeBg,
                border: `1px solid ${borderColor}`,
                fontSize: '12px',
                fontWeight: isCurrent ? '600' : '400',
                color: textColor,
                transition: 'all 0.2s ease'
              }}
            >
              <Icon size={16} color={iconColor} />
              <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {node.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
