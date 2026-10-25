import React from 'react';
import { Play, ShieldAlert, Sparkles, Youtube } from 'lucide-react';

export default function Header({ 
  channels, 
  currentChannel, 
  onSelectChannel, 
  jobs = [],
  currentJobId = '',
  onSelectJob = () => {},
  onNewVideo, 
  killSwitch, 
  onToggleKillSwitch,
  loading 
}) {
  return (
    <header className="glass-panel" style={{ padding: '16px 24px', marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{ background: 'linear-gradient(135deg, #EF4444 0%, #B91C1C 100%)', padding: '10px', borderRadius: '12px', display: 'flex' }}>
          <Youtube size={26} color="#FFFFFF" />
        </div>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: '700', letterSpacing: '-0.02em' }}>Faceless YouTube Studio</h1>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Multi-Agent Autonomous Production with Quality Gates</p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
        {/* Channel Dropdown */}
        <select 
          value={currentChannel} 
          onChange={e => onSelectChannel(e.target.value)}
          style={{
            background: '#131B2E',
            color: 'var(--text-main)',
            border: '1px solid var(--border)',
            padding: '8px 14px',
            borderRadius: '8px',
            fontSize: '14px',
            outline: 'none',
            cursor: 'pointer'
          }}
        >
          {channels.map(ch => (
            <option key={ch._id} value={ch._id}>
              {ch.name} ({ch.language_code || 'en-US'})
            </option>
          ))}
        </select>

        {/* Recent Jobs Dropdown */}
        {jobs && jobs.length > 0 && (
          <select
            value={currentJobId}
            onChange={e => onSelectJob(e.target.value)}
            style={{
              background: '#131B2E',
              color: '#38BDF8',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              padding: '8px 14px',
              borderRadius: '8px',
              fontSize: '13px',
              fontWeight: '600',
              outline: 'none',
              cursor: 'pointer'
            }}
          >
            {jobs.map(j => (
              <option key={j._id} value={j._id}>
                🎬 {j.custom_topic || j.title || j._id} ({j.status})
              </option>
            ))}
          </select>
        )}

        {/* Kill Switch Toggle */}
        <button 
          onClick={onToggleKillSwitch} 
          className={killSwitch ? "button-danger" : "button-secondary"}
          title="Emergency Stop: halts all pending and publishing videos immediately"
        >
          <ShieldAlert size={16} />
          {killSwitch ? "Kill Switch Active (Paused)" : "Kill Switch Armed"}
        </button>

        {/* Generate Video Action */}
        <button 
          onClick={onNewVideo} 
          disabled={loading}
          className="button-primary"
        >
          <Sparkles size={16} />
          {loading ? "Initializing..." : "New Video"}
        </button>
      </div>
    </header>
  );
}
