const BASE = '';

export const api = {
  getChannels: () => fetch(`${BASE}/channels`).then(r => r.json()),
  getChannel: id => fetch(`${BASE}/channels/${id}`).then(r => r.json()),
  saveChannel: body => fetch(`${BASE}/channels`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  }).then(r => r.json()),

  getJobs: () => fetch(`${BASE}/jobs`).then(r => r.json()),
  getJob: id => fetch(`${BASE}/jobs/${id}`).then(r => r.json()),
  createJob: body => fetch(`${BASE}/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  }).then(r => r.json()),

  resumeJob: (id, decision) => fetch(`${BASE}/jobs/${id}/resume`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(decision)
  }).then(r => r.json()),

  getKillSwitch: () => fetch(`${BASE}/kill-switch`).then(r => r.json()),
  setKillSwitch: on => fetch(`${BASE}/kill-switch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ on })
  }).then(r => r.json()),

  getCalendar: () => fetch(`${BASE}/calendar`).then(r => r.json()),

  generateShorts: (jobId) => fetch(`${BASE}/jobs/${jobId}/shorts`, {
    method: 'POST'
  }).then(r => r.json()),

  getCompetitors: (channelId) => fetch(`${BASE}/channels/${channelId}/competitors`).then(r => r.json()),

  triggerFanout: (jobId, targetChannels) => fetch(`${BASE}/jobs/${jobId}/fanout`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_channels: targetChannels })
  }).then(r => r.json()),

  getMonetization: (jobId) => fetch(`${BASE}/jobs/${jobId}/monetization`).then(r => r.json()),

  generateThumbnails: (jobId, headline) => fetch(`${BASE}/jobs/${jobId}/thumbnails`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ headline })
  }).then(r => r.json()),
};
