import React, { useState } from 'react';
import { Radio, Plus, Check } from 'lucide-react';

const INDIAN_LANGUAGES = [
  { code: 'hi-IN', label: 'Hindi (Devanagari)', yt: 'hi', script: 'Devanagari' },
  { code: 'en-IN', label: 'Indian English (Latin)', yt: 'en', script: 'Latin' },
  { code: 'bn-IN', label: 'Bengali', yt: 'bn', script: 'Bengali' },
  { code: 'ta-IN', label: 'Tamil', yt: 'ta', script: 'Tamil' },
  { code: 'te-IN', label: 'Telugu', yt: 'te', script: 'Telugu' },
  { code: 'kn-IN', label: 'Kannada', yt: 'kn', script: 'Kannada' },
  { code: 'ml-IN', label: 'Malayalam', yt: 'ml', script: 'Malayalam' },
  { code: 'mr-IN', label: 'Marathi', yt: 'mr', script: 'Devanagari' },
  { code: 'gu-IN', label: 'Gujarati', yt: 'gu', script: 'Gujarati' },
  { code: 'pa-IN', label: 'Punjabi', yt: 'pa', script: 'Gurmukhi' },
  { code: 'en-US', label: 'Global English (US)', yt: 'en', script: 'Latin' }
];

export default function ChannelsManager({ channels, onSaveChannel }) {
  const [name, setName] = useState('');
  const [niche, setNiche] = useState('Technology & Industrial Trends');
  const [langCode, setLangCode] = useState('hi-IN');
  const [provider, setProvider] = useState('sarvam');
  const [voice, setVoice] = useState('priya');
  const [mixingRule, setMixingRule] = useState('Hindi grammar, English technical terms kept in Latin script');
  const [targetMin, setTargetMin] = useState(8);
  const [savedMsg, setSavedMsg] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    const selectedLang = INDIAN_LANGUAGES.find(l => l.code === langCode);
    const newChan = {
      _id: name.toLowerCase().replace(/[^a-z0-9]/g, '_') || 'channel_' + Date.now(),
      name: name || 'Indian Tech Explainers',
      niche,
      language_code: langCode,
      youtube_lang: selectedLang?.yt || 'hi',
      script: selectedLang?.script || 'Devanagari',
      mixing_rule: mixingRule,
      tts_route: {
        provider,
        voice,
        pace: 1.0
      },
      target_minutes: Number(targetMin)
    };
    onSaveChannel(newChan);
    setSavedMsg(true);
    setTimeout(() => setSavedMsg(false), 3000);
  };

  return (
    <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
        <Radio size={20} color="#3B82F6" />
        <h2 style={{ fontSize: '18px', fontWeight: '700' }}>Channel Profiles & Indic Voice Hub</h2>
      </div>
      <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '20px' }}>
        Configure dedicated channel niches and native language models (Blueprint Section 7 & 21). One channel per language ensures high YouTube recommendation velocity.
      </p>

      <form onSubmit={handleSubmit} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        <div>
          <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)' }}>Channel Name</label>
          <input 
            type="text" 
            placeholder="e.g. Bharat Tech Insights" 
            value={name} 
            onChange={e => setName(e.target.value)} 
            style={{ width: '100%', marginTop: '6px', padding: '10px', background: '#0B0F19', border: '1px solid var(--border)', borderRadius: '8px', color: '#FFF' }}
          />
        </div>

        <div>
          <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)' }}>Niche & Topic Focus</label>
          <input 
            type="text" 
            value={niche} 
            onChange={e => setNiche(e.target.value)} 
            style={{ width: '100%', marginTop: '6px', padding: '10px', background: '#0B0F19', border: '1px solid var(--border)', borderRadius: '8px', color: '#FFF' }}
          />
        </div>

        <div>
          <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)' }}>Native Language & Script</label>
          <select 
            value={langCode} 
            onChange={e => setLangCode(e.target.value)} 
            style={{ width: '100%', marginTop: '6px', padding: '10px', background: '#0B0F19', border: '1px solid var(--border)', borderRadius: '8px', color: '#FFF' }}
          >
            {INDIAN_LANGUAGES.map(l => (
              <option key={l.code} value={l.code}>{l.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)' }}>TTS Provider</label>
          <select 
            value={provider} 
            onChange={e => setProvider(e.target.value)} 
            style={{ width: '100%', marginTop: '6px', padding: '10px', background: '#0B0F19', border: '1px solid var(--border)', borderRadius: '8px', color: '#FFF' }}
          >
            <option value="sarvam">Sarvam AI Bulbul v3 (Best for Indian Languages)</option>
            <option value="elevenlabs">ElevenLabs Multilingual v2</option>
            <option value="mock">Local Synthesizer (Zero Cost Dev Mode)</option>
          </select>
        </div>

        <div>
          <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)' }}>Hinglish / Language Mixing Rule</label>
          <input 
            type="text" 
            value={mixingRule} 
            onChange={e => setMixingRule(e.target.value)} 
            style={{ width: '100%', marginTop: '6px', padding: '10px', background: '#0B0F19', border: '1px solid var(--border)', borderRadius: '8px', color: '#FFF' }}
          />
        </div>

        <div>
          <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)' }}>Target Video Duration (Minutes)</label>
          <input 
            type="number" 
            value={targetMin} 
            onChange={e => setTargetMin(e.target.value)} 
            style={{ width: '100%', marginTop: '6px', padding: '10px', background: '#0B0F19', border: '1px solid var(--border)', borderRadius: '8px', color: '#FFF' }}
          />
        </div>

        <div style={{ gridColumn: '1 / -1', display: 'flex', alignItems: 'center', gap: '14px', marginTop: '8px' }}>
          <button type="submit" className="button-primary">
            <Plus size={16} /> Save / Register Channel
          </button>
          {savedMsg && (
            <span style={{ color: '#34D399', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Check size={16} /> Channel profile updated!
            </span>
          )}
        </div>
      </form>
    </div>
  );
}
