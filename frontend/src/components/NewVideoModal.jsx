import React, { useState } from 'react';
import { Sparkles, X, Palette, Clapperboard, Film, Globe, FileText, CheckCircle2, Video } from 'lucide-react';

const PRESETS = [
  {
    title: "How One Accidental Bug Almost Destroyed Wall Street",
    desc: "2D Cartoon Mystery • High Tension • Wall Street Chaos",
    style: "cartoon_story"
  },
  {
    title: "The Strange Secret of the Underground Internet Cables",
    desc: "Animated Deep-Sea Thriller • Sharks vs Fiber Optic Cables",
    style: "3d_pixar"
  },
  {
    title: "The 4-Year Machine That Is Freezing the AI Revolution",
    desc: "Tech Story Explainer • Giant Transformers & Microscopic Steel",
    style: "anime_graphic"
  }
];

export default function NewVideoModal({ isOpen, onClose, onSubmit, loading }) {
  const [mode, setMode] = useState("paste"); // "paste" or "research"
  const [content, setContent] = useState("");
  const [topic, setTopic] = useState("");
  const [style, setStyle] = useState("cartoon_story");
  const [targetMin, setTargetMin] = useState(3);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      topic: topic.trim() || undefined,
      content: mode === "paste" && content.trim() ? content.trim() : undefined,
      story_style: style,
      target_minutes: Number(targetMin)
    });
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(5, 8, 16, 0.85)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }}>
      <div className="glass-panel" style={{
        maxWidth: '680px',
        width: '100%',
        maxHeight: '92vh',
        overflowY: 'auto',
        padding: '26px',
        borderRadius: '16px',
        border: '1px solid rgba(59, 130, 246, 0.3)',
        boxShadow: '0 20px 50px rgba(0, 0, 0, 0.85)',
        position: 'relative'
      }}>
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer'
          }}
        >
          <X size={20} />
        </button>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
          <div style={{ background: 'linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)', padding: '8px', borderRadius: '10px' }}>
            <Sparkles size={20} color="#FFFFFF" />
          </div>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '700' }}>Create Faceless Video</h2>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Continuous Voiceover • Dynamic Ken Burns Pan/Zoom • Rich Sound Bed • Karaoke Captions
            </div>
          </div>
        </div>

        {/* Mode Switch Tabs */}
        <div style={{
          display: 'flex',
          gap: '8px',
          background: 'rgba(15, 23, 42, 0.6)',
          padding: '4px',
          borderRadius: '10px',
          border: '1px solid var(--border)',
          margin: '18px 0 20px 0'
        }}>
          <button
            type="button"
            onClick={() => setMode("paste")}
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '10px 14px',
              borderRadius: '8px',
              border: 'none',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer',
              background: mode === 'paste' ? 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)' : 'transparent',
              color: mode === 'paste' ? '#FFFFFF' : 'var(--text-muted)',
              transition: 'all 0.2s ease'
            }}
          >
            <FileText size={16} />
            Paste My Own Script / Story
          </button>
          
          <button
            type="button"
            onClick={() => setMode("research")}
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '10px 14px',
              borderRadius: '8px',
              border: 'none',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer',
              background: mode === 'research' ? 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)' : 'transparent',
              color: mode === 'research' ? '#FFFFFF' : 'var(--text-muted)',
              transition: 'all 0.2s ease'
            }}
          >
            <Globe size={16} />
            Live Web Research & Plan
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {/* TAB 1: PASTE MODE */}
          {mode === "paste" && (
            <>
              <div>
                <label style={{ fontSize: '13px', fontWeight: '600', color: '#E2E8F0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <FileText size={14} color="#3B82F6" />
                  Paste Your Full Script or Story Content
                </label>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px', marginBottom: '8px' }}>
                  Paste from ChatGPT, story draft, or article. 100% of your exact text, characters & dialogue will be used.
                </div>
                <textarea
                  required
                  rows={7}
                  placeholder={`Once upon a time in a secluded lab, an engineer noticed a glitch that defied physics...\n\nPaste your exact script or multi-paragraph story here. The AI will segment it scene-by-scene, generate cartoon visuals, and narrate the full voiceover continuously.`}
                  value={content}
                  onChange={e => setContent(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    background: '#0B0F19',
                    border: '1px solid var(--border)',
                    borderRadius: '8px',
                    color: '#FFF',
                    fontSize: '13px',
                    lineHeight: '1.5',
                    outline: 'none',
                    resize: 'vertical',
                    fontFamily: 'inherit'
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)' }}>
                  Story Title (Optional - AI will auto-detect from content if blank)
                </label>
                <input
                  type="text"
                  placeholder="e.g. The Secret of the Glitched Signal"
                  value={topic}
                  onChange={e => setTopic(e.target.value)}
                  style={{
                    width: '100%',
                    marginTop: '6px',
                    padding: '10px 12px',
                    background: '#0B0F19',
                    border: '1px solid var(--border)',
                    borderRadius: '8px',
                    color: '#FFF',
                    fontSize: '13px',
                    outline: 'none'
                  }}
                />
              </div>
            </>
          )}

          {/* TAB 2: LIVE WEB RESEARCH MODE */}
          {mode === "research" && (
            <>
              <div>
                <label style={{ fontSize: '13px', fontWeight: '600', color: '#E2E8F0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Globe size={14} color="#10B981" />
                  What Topic Should the AI Research on the Internet?
                </label>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px', marginBottom: '8px' }}>
                  The agent searches live web sources (Tavily/SerpApi) to find true viral facts, plans a 5-beat hook, and drafts the script.
                </div>
                <input
                  type="text"
                  placeholder="e.g. The Untold Story of How One Hacker Stole a Satellite..."
                  value={topic}
                  onChange={e => setTopic(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    background: '#0B0F19',
                    border: '1px solid var(--border)',
                    borderRadius: '8px',
                    color: '#FFF',
                    fontSize: '13px',
                    outline: 'none'
                  }}
                />
              </div>

              {/* Preset Viral Hooks */}
              <div>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: '600' }}>Or Pick High-Retention Story Preset:</span>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '6px' }}>
                  {PRESETS.map((p, idx) => (
                    <div
                      key={idx}
                      onClick={() => { setTopic(p.title); setStyle(p.style); }}
                      style={{
                        padding: '10px 14px',
                        background: topic === p.title ? 'rgba(59, 130, 246, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                        border: `1px solid ${topic === p.title ? '#3B82F6' : 'var(--border)'}`,
                        borderRadius: '8px',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      <div style={{ fontSize: '13px', fontWeight: '600', color: '#F8FAFC' }}>{p.title}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>{p.desc}</div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Visual Animation Style */}
          <div>
            <label style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-muted)', marginBottom: '8px', display: 'block' }}>
              Animation & Visual Style:
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '10px' }}>
              <div
                onClick={() => setStyle("cartoon_story")}
                style={{
                  padding: '12px',
                  background: style === 'cartoon_story' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                  border: `1px solid ${style === 'cartoon_story' ? '#10B981' : 'var(--border)'}`,
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                <Palette size={16} color="#10B981" />
                <div style={{ fontSize: '12px', fontWeight: '600', marginTop: '6px' }}>2D Cartoon Story</div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Kurzgesagt vector art</div>
              </div>

              <div
                onClick={() => setStyle("3d_pixar")}
                style={{
                  padding: '12px',
                  background: style === '3d_pixar' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                  border: `1px solid ${style === '3d_pixar' ? '#F59E0B' : 'var(--border)'}`,
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                <Clapperboard size={16} color="#F59E0B" />
                <div style={{ fontSize: '12px', fontWeight: '600', marginTop: '6px' }}>3D Pixar Animation</div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Cinematic character drama</div>
              </div>

              <div
                onClick={() => setStyle("anime_graphic")}
                style={{
                  padding: '12px',
                  background: style === 'anime_graphic' ? 'rgba(139, 92, 246, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                  border: `1px solid ${style === 'anime_graphic' ? '#8B5CF6' : 'var(--border)'}`,
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                <Film size={16} color="#8B5CF6" />
                <div style={{ fontSize: '12px', fontWeight: '600', marginTop: '6px' }}>Comic Book Mystery</div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Dramatic noir & sci-fi</div>
              </div>

              <div
                onClick={() => setStyle("stock_cinematic")}
                style={{
                  padding: '12px',
                  background: style === 'stock_cinematic' ? 'rgba(59, 130, 246, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                  border: `1px solid ${style === 'stock_cinematic' ? '#3B82F6' : 'var(--border)'}`,
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                <Video size={16} color="#3B82F6" />
                <div style={{ fontSize: '12px', fontWeight: '600', marginTop: '6px' }}>Cinematic Stock (Coverr)</div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Real 4K/HD video clips</div>
              </div>
            </div>
          </div>

          {/* Dynamic Motion & High Quality Engine Highlights */}
          <div style={{
            background: 'rgba(59, 130, 246, 0.08)',
            border: '1px solid rgba(59, 130, 246, 0.25)',
            borderRadius: '8px',
            padding: '10px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}>
            <CheckCircle2 size={18} color="#3B82F6" style={{ flexShrink: 0 }} />
            <div style={{ fontSize: '11px', color: '#93C5FD' }}>
              <strong>AI Multi-Agent Production Engine:</strong> ElevenLabs & Sarvam Hollywood Voiceover, Coverr & Pixabay 4K/HD Video Clips, YouTube Data v3 SEO Ranking Tags, Ken Burns camera motion, and synced subtitles.
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
            <button
              type="button"
              onClick={onClose}
              className="button-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || (mode === 'paste' && !content.trim())}
              className="button-primary"
              style={{
                background: (loading || (mode === 'paste' && !content.trim())) ? '#334155' : undefined,
                cursor: (loading || (mode === 'paste' && !content.trim())) ? 'not-allowed' : 'pointer'
              }}
            >
              <Sparkles size={16} />
              {loading ? "Agent Planning Pipeline..." : (mode === 'paste' ? "Create Video from Script" : "Generate Viral Story Video")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
