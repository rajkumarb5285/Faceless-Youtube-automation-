import React, { useState } from 'react';
import { Check, Edit3, XCircle, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function ScriptEditorModal({ job, onDecision, isWaiting }) {
  const script = job?.values?.script;
  const [scenes, setScenes] = useState(script?.scenes || []);
  const claims = Object.fromEntries((job?.values?.claims || []).map(c => [c.id, c]));

  if (!script) {
    return (
      <div className="glass-panel" style={{ padding: '24px', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-muted)' }}>Script has not been generated yet.</p>
      </div>
    );
  }

  const totalWords = scenes.reduce((acc, s) => acc + (s.narration?.split(/\s+/).filter(Boolean).length || 0), 0);

  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid var(--border)', paddingBottom: '14px' }}>
        <div>
          <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#F59E0B', fontWeight: '700' }}>
            Quality Gate 1 • Script Review
          </span>
          <h2 style={{ fontSize: '18px', fontWeight: '700', marginTop: '4px' }}>{script.title}</h2>
        </div>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
            Total Words: <b>{totalWords}</b>
          </span>
          {job?.values?.critic && (
            <span style={{ 
              fontSize: '12px', 
              background: 'rgba(16, 185, 129, 0.15)', 
              color: '#34D399', 
              padding: '4px 10px', 
              borderRadius: '8px' 
            }}>
              Critic Traceability: {job.values.critic.scores?.traceability || 10}/10
            </span>
          )}
        </div>
      </div>

      {/* Scenes List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxHeight: '500px', overflowY: 'auto', paddingRight: '8px' }}>
        {scenes.map((sc, i) => (
          <div 
            key={sc.idx} 
            style={{ 
              background: 'rgba(255, 255, 255, 0.02)', 
              border: '1px solid var(--border)', 
              borderRadius: '10px', 
              padding: '14px' 
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: '600', color: '#60A5FA' }}>
                Scene {sc.idx} • {sc.visual_intent || 'Standard Shot'}
              </span>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Pace: {sc.pace} {sc.pattern_interrupt ? '• [Pattern Interrupt]' : ''}
              </span>
            </div>

            <textarea
              rows={3}
              value={sc.narration}
              onChange={e => {
                const nextScenes = [...scenes];
                nextScenes[i] = { ...nextScenes[i], narration: e.target.value };
                setScenes(nextScenes);
              }}
              style={{
                width: '100%',
                background: '#0B0F19',
                color: 'var(--text-main)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '10px',
                fontSize: '14px',
                fontFamily: 'inherit',
                resize: 'vertical'
              }}
            />

            {/* Claims Verification status badges */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '8px', alignItems: 'center' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Claims:</span>
              {sc.claim_ids?.length > 0 ? (
                sc.claim_ids.map(cid => {
                  const claim = claims[cid];
                  const status = claim ? claim.status : 'missing';
                  let chipClass = 'chip-weak';
                  if (status === 'verified') chipClass = 'chip-verified';
                  if (status === 'rejected' || status === 'missing') chipClass = 'chip-rejected';

                  return (
                    <span 
                      key={cid} 
                      className={chipClass}
                      title={claim ? claim.text : 'Unknown claim ID'}
                      style={{ padding: '2px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: '500' }}
                    >
                      {cid} ({status})
                    </span>
                  );
                })
              ) : (
                <span style={{ fontSize: '11px', color: '#94A3B8', fontStyle: 'italic' }}>
                  No quantitative claims cited
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Action Decision Buttons */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border)' }}>
        <button 
          onClick={() => onDecision({ action: 'reject' })}
          className="button-danger"
        >
          <XCircle size={16} />
          Reject Topic / Script
        </button>

        <button 
          onClick={() => onDecision({ action: 'edit', script: { ...script, scenes, total_words: totalWords } })}
          className="button-secondary"
        >
          <Edit3 size={16} />
          Save Edits & Continue
        </button>

        <button 
          onClick={() => onDecision({ action: 'approve' })}
          className="button-primary"
        >
          <Check size={16} />
          Approve As Is
        </button>
      </div>
    </div>
  );
}
