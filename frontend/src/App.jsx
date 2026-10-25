import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import PipelineTimeline from './components/PipelineTimeline';
import ScriptEditorModal from './components/ScriptEditorModal';
import QAPlayerModal from './components/QAPlayerModal';
import ChannelsManager from './components/ChannelsManager';
import ShortsViewer from './components/ShortsViewer';
import MonetizationTab from './components/MonetizationTab';
import NewVideoModal from './components/NewVideoModal';
import { api } from './api';
import { Sparkles, Layers, BarChart2, Radio, Smartphone, DollarSign, CheckCircle, Info } from 'lucide-react';

export default function App() {
  const [channels, setChannels] = useState([]);
  const [channelId, setChannelId] = useState('default');
  const [jobId, setJobId] = useState(() => localStorage.getItem('faceless_job_id') || '');
  const [job, setJob] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [killSwitch, setKillSwitch] = useState(false);
  const [activeTab, setActiveTab] = useState('pipeline');
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const refreshJobsList = () => {
    api.getJobs().then(jList => {
      if (jList?.length) {
        setJobs(jList);
        if (!jobId) {
          const latest = jList[jList.length - 1];
          setJobId(latest._id);
          localStorage.setItem('faceless_job_id', latest._id);
        }
      }
    }).catch(console.error);
  };

  // Load channels, jobs & kill-switch status on mount
  useEffect(() => {
    api.getChannels().then(chans => {
      if (chans?.length) {
        setChannels(chans);
        if (!chans.find(c => c._id === channelId)) {
          setChannelId(chans[0]._id);
        }
      }
    }).catch(console.error);

    refreshJobsList();

    api.getKillSwitch().then(res => {
      setKillSwitch(res.kill_switch_active);
    }).catch(console.error);
  }, []);

  // Poll job data
  useEffect(() => {
    if (!jobId) return;
    const fetchJob = () => {
      api.getJob(jobId)
        .then(data => setJob(data))
        .catch(console.error);
    };

    fetchJob();
    const interval = setInterval(fetchJob, 2500);
    return () => clearInterval(interval);
  }, [jobId]);

  const handleStartStoryVideo = async (params) => {
    setLoading(true);
    setShowModal(false);
    try {
      const res = await api.createJob({ 
        channel_id: channelId, 
        autonomy: 1,
        topic: params.topic,
        content: params.content,
        story_style: params.story_style,
        target_minutes: params.target_minutes
      });
      setJobId(res.job_id);
      localStorage.setItem('faceless_job_id', res.job_id);
      setActiveTab('pipeline');
    } catch (err) {
      alert("Error starting story job: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (decision) => {
    if (!jobId) return;
    try {
      await api.resumeJob(jobId, decision);
      // Immediate refresh
      const updated = await api.getJob(jobId);
      setJob(updated);
    } catch (err) {
      alert("Failed to submit decision: " + err.message);
    }
  };

  const handleToggleKillSwitch = async () => {
    const nextState = !killSwitch;
    await api.setKillSwitch(nextState);
    setKillSwitch(nextState);
  };

  const handleSaveChannel = async (newChan) => {
    await api.saveChannel(newChan);
    const updated = await api.getChannels();
    setChannels(updated);
  };

  const currentStep = job?.current_node || 'strategist';
  const isScriptGate = job?.status === 'waiting_human' || currentStep === 'human_review' || job?.next?.includes('human_review');
  const isQAGate = currentStep === 'qa_gate' || job?.next?.includes('qa_gate');

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '24px 20px' }}>
      <Header
        channels={channels}
        currentChannel={channelId}
        onSelectChannel={setChannelId}
        jobs={jobs}
        currentJobId={jobId}
        onSelectJob={(id) => {
          setJobId(id);
          localStorage.setItem('faceless_job_id', id);
        }}
        onNewVideo={() => setShowModal(true)}
        killSwitch={killSwitch}
        onToggleKillSwitch={handleToggleKillSwitch}
        loading={loading}
      />

      <NewVideoModal 
        isOpen={showModal} 
        onClose={() => setShowModal(false)} 
        onSubmit={handleStartStoryVideo} 
        loading={loading} 
      />

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button 
          onClick={() => setActiveTab('pipeline')}
          className={activeTab === 'pipeline' ? "button-primary" : "button-secondary"}
        >
          <Layers size={16} /> Production Pipeline
        </button>
        <button 
          onClick={() => setActiveTab('channels')}
          className={activeTab === 'channels' ? "button-primary" : "button-secondary"}
        >
          <Radio size={16} /> Channels & Indic Voices
        </button>
        <button 
          onClick={() => setActiveTab('shorts')}
          className={activeTab === 'shorts' ? "button-primary" : "button-secondary"}
        >
          <Smartphone size={16} /> YouTube Shorts (9:16)
        </button>
        <button 
          onClick={() => setActiveTab('monetization')}
          className={activeTab === 'monetization' ? "button-primary" : "button-secondary"}
        >
          <DollarSign size={16} /> Monetization & Thumbnails
        </button>
        <button 
          onClick={() => setActiveTab('analytics')}
          className={activeTab === 'analytics' ? "button-primary" : "button-secondary"}
        >
          <BarChart2 size={16} /> Analytics & Learning Loop
        </button>
      </div>

      {activeTab === 'monetization' && (
        <MonetizationTab jobId={jobId} />
      )}

      {activeTab === 'shorts' && (
        <ShortsViewer 
          jobId={jobId} 
          channels={channels} 
          hasRenderedVideo={Boolean(job?.values?.render)} 
        />
      )}

      {activeTab === 'channels' && (
        <ChannelsManager channels={channels} onSaveChannel={handleSaveChannel} />
      )}

      {activeTab === 'analytics' && (
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '8px' }}>
            YouTube Analytics & Style Guide Optimizer (Blueprint 12 & 13)
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '20px' }}>
            The Analyst agent evaluates 24h, 72h, and 7d retention curves. Findings automatically update the channel prompt rules for subsequent video generations.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
            <div style={{ padding: '16px', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border)', borderRadius: '10px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Average View Duration</div>
              <div style={{ fontSize: '24px', fontWeight: '700', marginTop: '6px', color: '#34D399' }}>68.4%</div>
              <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '4px' }}>+12% above channel benchmark</div>
            </div>
            <div style={{ padding: '16px', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border)', borderRadius: '10px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Click-Through Rate (CTR)</div>
              <div style={{ fontSize: '24px', fontWeight: '700', marginTop: '6px', color: '#60A5FA' }}>7.8%</div>
              <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '4px' }}>Top title variant performing well</div>
            </div>
            <div style={{ padding: '16px', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border)', borderRadius: '10px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Automated Style Guide Rules</div>
              <div style={{ fontSize: '14px', fontWeight: '600', marginTop: '8px', color: '#FBBF24' }}>
                "Place numeric reveal at second 25 to halt retention drops"
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'pipeline' && (
        <>
          {/* Active Job Progress Visualizer */}
          <PipelineTimeline 
            currentStep={currentStep} 
            waitingGate={isScriptGate || isQAGate} 
            status={job?.status} 
          />

          {/* Current Topic & Thesis Banner */}
          {job?.values?.topic && (
            <div className="glass-panel" style={{ padding: '20px 24px', marginBottom: '24px', borderLeft: '4px solid #3B82F6' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#60A5FA', fontWeight: '700' }}>
                  Selected Topic Thesis
                </span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Job ID: <code style={{ color: '#F8FAFC' }}>{job.job_id}</code>
                </span>
              </div>
              <h2 style={{ fontSize: '18px', fontWeight: '700', marginTop: '6px' }}>
                {job.values.topic.topic}
              </h2>
              <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginTop: '4px' }}>
                {job.values.topic.thesis}
              </p>
            </div>
          )}

          {/* Quality Gate 1: Script Review */}
          {(isScriptGate || job?.values?.script) && (
            <ScriptEditorModal 
              job={job} 
              onDecision={handleDecision} 
              isWaiting={isScriptGate} 
            />
          )}

          {/* Quality Gate 2: Final Video Render Review */}
          {(isQAGate || job?.values?.render) && (
            <QAPlayerModal 
              job={job} 
              onDecision={handleDecision} 
            />
          )}
        </>
      )}
    </div>
  );
}
