import React, { useState, useEffect } from 'react';
import { DollarSign, Award, Target, Mail, Copy, Check, Image as ImageIcon, Sparkles } from 'lucide-react';
import { api } from '../api';

export default function MonetizationTab({ jobId }) {
  const [data, setData] = useState(null);
  const [thumbnails, setThumbnails] = useState([]);
  const [copiedPitch, setCopiedPitch] = useState(false);
  const [generatingThumbs, setGeneratingThumbs] = useState(false);
  const [thumbHeadline, setThumbHeadline] = useState("THE 4-YEAR CHOKE");

  useEffect(() => {
    if (!jobId) return;
    api.getMonetization(jobId).then(setData).catch(console.error);
  }, [jobId]);

  const handleGenerateThumbs = async () => {
    if (!jobId) return;
    setGeneratingThumbs(true);
    try {
      const res = await api.generateThumbnails(jobId, thumbHeadline);
      setThumbnails(res.variants || []);
    } catch (err) {
      alert("Failed to generate thumbnail variants: " + err.message);
    } finally {
      setGeneratingThumbs(false);
    }
  };

  const handleCopyPitch = () => {
    if (data?.sponsor_pitch?.drafted_email_pitch) {
      navigator.clipboard.writeText(data.sponsor_pitch.drafted_email_pitch);
      setCopiedPitch(true);
      setTimeout(() => setCopiedPitch(false), 3000);
    }
  };

  const ypp = data?.ypp_tracker;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* 3 High-CTR Thumbnail Templates Generator (Blueprint 6.10) */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ImageIcon size={20} color="#F59E0B" />
            <h2 style={{ fontSize: '18px', fontWeight: '700' }}>3 High-CTR Thumbnail Templates (Blueprint 6.10)</h2>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <input 
              type="text"
              value={thumbHeadline}
              onChange={e => setThumbHeadline(e.target.value)}
              placeholder="3-Word Headline"
              style={{
                background: '#0B0F19',
                color: '#FFF',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '6px 12px',
                fontSize: '13px'
              }}
            />
            <button 
              onClick={handleGenerateThumbs}
              disabled={generatingThumbs || !jobId}
              className="button-primary"
            >
              <Sparkles size={16} />
              {generatingThumbs ? "Generating..." : "Render 3 Variants"}
            </button>
          </div>
        </div>

        <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
          Strictly preserves the 1280x720 canvas safe zone (avoids the bottom-right corner where YouTube places duration overlays).
        </p>

        {thumbnails.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
            {thumbnails.map(t => (
              <div key={t.template_id} style={{ background: '#0B0F19', borderRadius: '10px', overflow: 'hidden', border: '1px solid var(--border)' }}>
                <img src={t.url} alt={`Template ${t.template_id}`} style={{ width: '100%', height: 'auto', display: 'block' }} />
                <div style={{ padding: '10px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)' }}>
                    Template {t.template_id}: {t.template_id === 1 ? 'Split Contrast' : t.template_id === 2 ? 'Neon Spotlight' : 'Stat Shock'}
                  </span>
                  <a href={t.url} download className="button-secondary" style={{ fontSize: '11px', textDecoration: 'none' }}>
                    Download
                  </a>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ padding: '30px', textAlign: 'center', background: 'rgba(255,255,255,0.02)', borderRadius: '10px', border: '1px dashed var(--border)' }}>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Click <b>Render 3 Variants</b> to produce Split-Contrast, Neon Spotlight, and Stat Shock thumbnails.</p>
          </div>
        )}
      </div>

      {/* YouTube Partner Program Progress Tracker */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <Target size={20} color="#10B981" />
          <h2 style={{ fontSize: '18px', fontWeight: '700' }}>YouTube Partner Program Tracking (Blueprint 13)</h2>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
          {/* Tier 1 */}
          <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)', borderRadius: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '12px', fontWeight: '700', color: '#F59E0B' }}>TIER 1 • FAN FUNDING</span>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>500 Subs / 3,000 Hours</span>
            </div>
            <div style={{ marginTop: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                <span>Subscribers</span>
                <b>{ypp?.tier_1_fan_funding?.subscribers?.current || 420} / 500</b>
              </div>
              <div style={{ height: '6px', background: '#1E293B', borderRadius: '3px', marginTop: '6px' }}>
                <div style={{ width: '84%', height: '100%', background: '#F59E0B', borderRadius: '3px' }} />
              </div>
            </div>
            <div style={{ marginTop: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                <span>Watch Hours</span>
                <b>{ypp?.tier_1_fan_funding?.watch_hours?.current || 2450} / 3,000</b>
              </div>
              <div style={{ height: '6px', background: '#1E293B', borderRadius: '3px', marginTop: '6px' }}>
                <div style={{ width: '81.6%', height: '100%', background: '#F59E0B', borderRadius: '3px' }} />
              </div>
            </div>
          </div>

          {/* Tier 2 */}
          <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)', borderRadius: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '12px', fontWeight: '700', color: '#10B981' }}>TIER 2 • AD REVENUE (ADSENSE)</span>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>1,000 Subs / 4,000 Hours</span>
            </div>
            <div style={{ marginTop: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                <span>Subscribers</span>
                <b>{ypp?.tier_2_ad_revenue?.subscribers?.current || 420} / 1,000</b>
              </div>
              <div style={{ height: '6px', background: '#1E293B', borderRadius: '3px', marginTop: '6px' }}>
                <div style={{ width: '42%', height: '100%', background: '#10B981', borderRadius: '3px' }} />
              </div>
            </div>
            <div style={{ marginTop: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                <span>Watch Hours</span>
                <b>{ypp?.tier_2_ad_revenue?.watch_hours?.current || 2450} / 4,000</b>
              </div>
              <div style={{ height: '6px', background: '#1E293B', borderRadius: '3px', marginTop: '6px' }}>
                <div style={{ width: '61.2%', height: '100%', background: '#10B981', borderRadius: '3px' }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Sponsor Pitch Kit & Affiliate Links */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Mail size={20} color="#3B82F6" />
            <h2 style={{ fontSize: '18px', fontWeight: '700' }}>Sponsor Outreach Pitch & Affiliate Compliance</h2>
          </div>
          <button onClick={handleCopyPitch} className="button-secondary">
            {copiedPitch ? <Check size={16} color="#10B981" /> : <Copy size={16} />}
            {copiedPitch ? "Pitch Copied!" : "Copy Pitch Template"}
          </button>
        </div>

        <pre style={{
          background: '#0B0F19',
          padding: '16px',
          borderRadius: '8px',
          border: '1px solid var(--border)',
          color: '#E2E8F0',
          fontSize: '13px',
          fontFamily: 'inherit',
          whiteSpace: 'pre-wrap',
          marginBottom: '16px'
        }}>
          {data?.sponsor_pitch?.drafted_email_pitch || "Generating sponsor media kit..."}
        </pre>

        {/* Affiliate links checklist */}
        <h4 style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-muted)', marginBottom: '8px' }}>
          AUTOMATED AFFILIATE LINKS & DISCLOSURE
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {data?.affiliate_links?.map((aff, i) => (
            <div key={i} style={{ padding: '10px 14px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)', borderRadius: '8px', fontSize: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <b style={{ color: '#60A5FA' }}>{aff.product}</b>
                <span style={{ color: 'var(--text-muted)' }}>Placement: {aff.placement}</span>
              </div>
              <p style={{ marginTop: '4px', color: '#94A3B8' }}>{aff.disclosure}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
