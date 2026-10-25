import React, { useState } from 'react';
import { Smartphone, Sparkles, Download, Globe2, CheckCircle2, Play } from 'lucide-react';
import { api } from '../api';

export default function ShortsViewer({ jobId, channels, hasRenderedVideo }) {
  const [generating, setGenerating] = useState(false);
  const [shortData, setShortData] = useState(null);
  const [fanoutDone, setFanoutDone] = useState(false);
  const [selectedChannels, setSelectedChannels] = useState([]);

  const handleGenerateShorts = async () => {
    if (!jobId) return;
    setGenerating(true);
    try {
      const res = await api.generateShorts(jobId);
      setShortData(res);
    } catch (err) {
      alert("Error generating Short: " + err.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleFanout = async () => {
    if (!jobId || selectedChannels.length === 0) return;
    try {
      await api.triggerFanout(jobId, selectedChannels);
      setFanoutDone(true);
      setTimeout(() => setFanoutDone(false), 4000);
    } catch (err) {
      alert("Error triggering multilingual fan-out: " + err.message);
    }
  };

  const videoUrl = shortData?.short_path ? `/media/${jobId}/short_1/final_short.mp4` : null;

  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Smartphone size={20} color="#F59E0B" />
          <h2 style={{ fontSize: '18px', fontWeight: '700' }}>YouTube Shorts (9:16) & Multilingual Studio</h2>
        </div>
        <button
          onClick={handleGenerateShorts}
          disabled={generating || !jobId}
          className="button-primary"
        >
          <Sparkles size={16} />
          {generating ? "Rendering 9:16 Short..." : "Extract & Render Short (1080x1920)"}
        </button>
      </div>

      <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '20px' }}>
        Per Blueprint Section 2 & 12, each 8–12 minute explainer automatically yields 2 to 3 discovery Shorts rendered as separate 9:16 vertical timelines (not a center-crop of long-form).
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
        {/* Smartphone Preview Mockup */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{
            width: '270px',
            height: '480px',
            background: '#000000',
            borderRadius: '32px',
            border: '6px solid #1E293B',
            boxShadow: '0 12px 36px rgba(0,0,0,0.6)',
            position: 'relative',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {videoUrl ? (
              <video 
                src={videoUrl} 
                controls 
                autoPlay 
                loop 
                style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
              />
            ) : (
              <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)' }}>
                <Smartphone size={40} color="#334155" style={{ marginBottom: '12px' }} />
                <p style={{ fontSize: '13px' }}>Click <b>Extract & Render Short</b> to preview the 9:16 timeline.</p>
              </div>
            )}
          </div>
          {shortData && (
            <div style={{ marginTop: '14px', display: 'flex', gap: '10px' }}>
              <a 
                href={videoUrl} 
                download 
                className="button-secondary" 
                style={{ fontSize: '12px', textDecoration: 'none' }}
              >
                <Download size={14} /> Download 9:16 MP4
              </a>
            </div>
          )}
        </div>

        {/* Multilingual Fan-Out Section (Blueprint 21.10) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Globe2 size={18} color="#3B82F6" />
            <h3 style={{ fontSize: '15px', fontWeight: '600' }}>Multi-Language Fan-Out (Blueprint 21.10)</h3>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
            One verified claims table can produce localized native scripts across Hindi, Tamil, Telugu, and English channels.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {channels.map(ch => (
              <label 
                key={ch._id} 
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '10px', 
                  padding: '10px 14px', 
                  background: 'rgba(255,255,255,0.02)', 
                  border: '1px solid var(--border)', 
                  borderRadius: '8px', 
                  cursor: 'pointer' 
                }}
              >
                <input 
                  type="checkbox"
                  checked={selectedChannels.includes(ch._id)}
                  onChange={e => {
                    if (e.target.checked) {
                      setSelectedChannels([...selectedChannels, ch._id]);
                    } else {
                      setSelectedChannels(selectedChannels.filter(id => id !== ch._id));
                    }
                  }}
                />
                <span style={{ fontSize: '13px', fontWeight: '500' }}>
                  {ch.name} <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>({ch.language_code || 'en-US'} - {ch.mixing_rule || 'Native'})</span>
                </span>
              </label>
            ))}
          </div>

          <button 
            onClick={handleFanout}
            disabled={selectedChannels.length === 0 || !jobId}
            className="button-primary"
            style={{ marginTop: 'auto' }}
          >
            <Globe2 size={16} /> Fan-Out to {selectedChannels.length} Language Channels
          </button>

          {fanoutDone && (
            <div style={{ color: '#34D399', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CheckCircle2 size={16} /> Child jobs dispatched to Planner!
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
