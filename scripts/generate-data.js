#!/usr/bin/env node
/**
 * RADAR data.json generator
 * Pulls from Amplitude, Slack, Linear
 * Synthesizes team/customer/decision context via Claude
 * Run: node generate-data.js [output-path]
 */

const fs = require('fs');

// --- CONFIG ---
const AMPLITUDE_CHARTS = {
  dau: 'a08uik9s',
  newUsers: 'u5ctmoro', 
  featureAdoption: '5ab27lld',
  retention: 'dogczzd8',
  collaboration: 'e74ntz32',
  engagement: '1v3107dq',
  sessionDuration: 'pepuaofo',
  keyActions: 'pr53xnu5',
};

const SLACK_CHANNELS = [
  // Product & leadership
  { id: 'C0A779UAY8P', name: '#product' },
  { id: 'C08LNSRG2MU', name: '#product-team' },
  { id: 'C099VTZA8G2', name: '#product-mdma' },
  { id: 'C07V8N850RK', name: '#product-release' },
  { id: 'C049F933D7C', name: '#product-ideas' },
  { id: 'C04LAUHFLTX', name: '#product-market-intel' },
  { id: 'C08MKM3HSF6', name: '#product-roadmap' },
  { id: 'C07V9L589RT', name: '#product-design' },
  // Engineering
  { id: 'C0464JXMVMJ', name: '#eng-team' },
  { id: 'C04KZ3J5ZNK', name: '#eng-bugs' },
  { id: 'C080J4P6F63', name: '#eng-help' },
  // Squads
  { id: 'C0A2RA3518C', name: '#eng-infra-squad' },
  { id: 'C0ACH15DACA', name: '#eng-sik-squad' },
  { id: 'C06QA1GH1B9', name: '#eng-rdi-squad' },
  { id: 'C095XPU779D', name: '#eng-gna-team' },
  { id: 'C098PHNDZGF', name: '#eng-canvas' },
  { id: 'C09BURW9F7D', name: '#eng-abac' },
  { id: 'C096YA0L4Q7', name: '#eng-e2' },
  { id: 'C0ACXS3TER4', name: '#eng-timeseries-data' },
  // GTM & support
  { id: 'C04M70TRKFY', name: '#eng-customer-support' },
  { id: 'C08VDGPEEPP', name: '#customer-asks' },
  { id: 'C06H3EM89SS', name: '#gtm-sales' },
  { id: 'C0810HWSV4M', name: '#gtm-sales-alerts' },
  { id: 'C08PU6TRMSA', name: '#gtm-feedback' },
  // Company
  { id: 'C03E58EKZQB', name: '#admin-general' },
  { id: 'C0AAWCX284X', name: '#admin-weekly-notes' },
  // Key customer channels
  { id: 'C05GKMLAB8X', name: '#ext-sift-k2' },
  { id: 'C05PJGX4CE8', name: '#ext-sift-astranis' },
  { id: 'C04S5URE1HR', name: '#ext-sift-parallel' },
  { id: 'C09QBK3CURM', name: '#ext-sift-varda' },
  { id: 'C090W0P5V9R', name: '#ext-sift-heart' },
  { id: 'C09TA1U7KFX', name: '#ext-sift-dust-moto' },
  { id: 'C0A7AU7TD5X', name: '#ext-sift-inversion' },
  { id: 'C09DS0EJNPP', name: '#ext-sift-orbitaloperations' },
  { id: 'C09PAJEAX2N', name: '#ext-sift-arbor-energy' },
  { id: 'C0AB7629Z9B', name: '#ext-sift-synnax' },
  { id: 'C09PHN5L6RY', name: '#ext-sift-zipline' },
  { id: 'C08B1T9AYS2', name: '#ext-sift-revel' },
];

const TEAM = [
  { name: 'Sanghee', role: 'PM', squad: 'Core Platform' },
  { name: 'Kenn', role: 'PM', squad: 'Data Access & Governance' },
  { name: 'Jess', role: 'PM', squad: 'Canvas & Workflows' },
  { name: 'Rowen', role: 'PM', squad: 'Infrastructure & Security' },
  { name: 'Kevin', role: 'Software Engineering Manager', squad: 'Engineering' },
  { name: 'Gui', role: 'FDE Lead', squad: 'Field Engineering' },
];

const COFOUNDERS = [
  { name: 'Austin', role: 'CEO' },
  { name: 'Karthik', role: 'CTO' },
];

const CUSTOMERS = [
  'K2 Space', 'Astranis', 'Reliable Robotics', 'Varda', 'Heart Aerospace',
  'Lockheed Martin', 'ULA', 'Parallel Systems', 'The Exploration Company',
  'OHB', 'Dust Moto', 'Orbital Operations', 'Inversion Space',
  'Revel', 'CX2', 'Also', 'Arbor Energy', 'Synnax', 'OdysAviation',
  'CriticalLoop', 'RadTeam', 'Starpath', 'Astrolab', 'AstroMecha',
  'Neros', 'Zipline', 'PlantD', 'Halo One', 'First Resonance',
  'Manufacturo', 'AstroForge', 'Exdanris',
];

// --- HELPERS ---
async function fetchJSON(url, opts = {}) {
  const r = await fetch(url, opts);
  if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
  return r.json();
}

// Attempt to repair truncated JSON
function repairJSON(text) {
  let clean = text.replace(/```json\s*/g, '').replace(/```\s*/g, '').trim();
  try { return JSON.parse(clean); } catch(e) {}
  // Try closing open structures
  let depth = 0, inStr = false, escape = false;
  for (const ch of clean) {
    if (escape) { escape = false; continue; }
    if (ch === '\\') { escape = true; continue; }
    if (ch === '"') { inStr = !inStr; continue; }
    if (inStr) continue;
    if (ch === '{' || ch === '[') depth++;
    if (ch === '}' || ch === ']') depth--;
  }
  // Close any open strings and structures
  if (inStr) clean += '"';
  while (depth > 0) {
    // Guess what to close based on last opener
    const lastOpen = clean.lastIndexOf('{') > clean.lastIndexOf('[') ? '}' : ']';
    clean += lastOpen;
    depth--;
  }
  try { return JSON.parse(clean); } catch(e2) {
    console.warn('[repair] Could not repair JSON:', e2.message);
    return null;
  }
}

// --- AMPLITUDE ---
async function pullAmplitude() {
  const key = process.env.AMPLITUDE_API_KEY;
  const secret = process.env.AMPLITUDE_SECRET;
  if (!key || !secret) { console.warn('[amp] No credentials, skipping'); return null; }
  
  const auth = Buffer.from(`${key}:${secret}`).toString('base64');
  const results = {};
  
  for (const [name, chartId] of Object.entries(AMPLITUDE_CHARTS)) {
    try {
      const data = await fetchJSON(
        `https://amplitude.com/api/3/chart/${chartId}/query`,
        { headers: { Authorization: `Basic ${auth}` } }
      );
      results[name] = { chart: chartId, data: data.data || data };
      console.log(`[amp] ✓ ${name}`);
    } catch (e) {
      console.warn(`[amp] ✗ ${name}: ${e.message}`);
    }
  }
  return results;
}

// --- SLACK ---
async function pullSlack() {
  const token = process.env.SLACK_BOT_TOKEN;
  if (!token) { console.warn('[slack] No token, skipping'); return []; }
  
  const signals = [];
  const since = Math.floor(Date.now() / 1000) - (3 * 86400);
  
  for (const ch of SLACK_CHANNELS) {
    try {
      const data = await fetchJSON(
        `https://slack.com/api/conversations.history?channel=${ch.id}&oldest=${since}&limit=50`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (data.ok && data.messages) {
        for (const msg of data.messages) {
          if (msg.subtype || !msg.text || msg.text.length < 20) continue;
          signals.push({
            source: 'slack', channel: ch.name,
            text: msg.text.slice(0, 500), user: msg.user,
            timestamp: new Date(msg.ts * 1000).toISOString(),
            evidence: [{ label: `Slack: ${ch.name}`,
              url: `https://siftstack.slack.com/archives/${ch.id}/p${msg.ts.replace('.', '')}`,
              source: 'slack' }],
          });
        }
        console.log(`[slack] ✓ ${ch.name}: ${data.messages.length} messages`);
      }
    } catch (e) { console.warn(`[slack] ✗ ${ch.name}: ${e.message}`); }
  }
  return signals;
}

// --- LINEAR ---
async function pullLinear() {
  const key = process.env.LINEAR_API_KEY;
  if (!key) { console.warn('[linear] No key, skipping'); return []; }
  
  const signals = [];
  try {
    const data = await fetchJSON('https://api.linear.app/graphql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: key },
      body: JSON.stringify({
        query: `{ issues(filter: { state: { type: { in: ["started", "unstarted"] } }, priority: { lte: 2 } }, first: 30, orderBy: updatedAt) {
          nodes { identifier title priority state { name } assignee { name } team { name } updatedAt url labels { nodes { name } } } } }`
      }),
    });
    if (data.data?.issues?.nodes) {
      for (const issue of data.data.issues.nodes) {
        signals.push({
          source: 'linear', title: issue.identifier + ': ' + issue.title,
          priority: issue.priority <= 1 ? 'URGENT' : 'HIGH',
          state: issue.state?.name, assignee: issue.assignee?.name,
          team: issue.team?.name, timestamp: issue.updatedAt,
          evidence: [{ label: issue.identifier, url: issue.url, source: 'linear' }],
        });
      }
      console.log(`[linear] ✓ ${data.data.issues.nodes.length} issues`);
    }
  } catch (e) { console.warn(`[linear] ✗ ${e.message}`); }
  
  // Also pull active projects (Annual Roadmap view equivalent)
  try {
    const projData = await fetchJSON('https://api.linear.app/graphql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: key },
      body: JSON.stringify({
        query: `{ projects(filter: { state: { type: { in: ["started", "planned", "backlog"] } } }, first: 50, orderBy: updatedAt) {
          nodes { id name summary url startDate targetDate 
            status { name } priority { name value }
            lead { name } 
            teams { nodes { name key } }
            initiatives { nodes { name } }
            issues { nodes { identifier state { name type } priority } }
          } } }`
      }),
    });
    if (projData.data?.projects?.nodes) {
      const projects = projData.data.projects.nodes;
      for (const proj of projects) {
        const issues = proj.issues?.nodes || [];
        const inProgress = issues.filter(i => i.state?.type === 'started').length;
        const blocked = issues.filter(i => i.priority?.value <= 1).length;
        signals.push({
          source: 'linear', type: 'project',
          title: proj.name,
          status: proj.status?.name,
          priority: proj.priority?.name || 'Medium',
          lead: proj.lead?.name,
          team: proj.teams?.nodes?.[0]?.name,
          initiative: proj.initiatives?.nodes?.[0]?.name,
          startDate: proj.startDate,
          targetDate: proj.targetDate,
          issueCount: issues.length,
          inProgress, blocked,
          timestamp: proj.targetDate || proj.startDate,
          evidence: [{ label: proj.name, url: proj.url, source: 'linear' }],
        });
      }
      console.log(`[linear] ✓ ${projects.length} projects (roadmap)`);
    }
  } catch (e) { console.warn(`[linear] ✗ projects: ${e.message}`); }
  
  return signals;
}

// --- SYNTHESIZE via Claude (split into smaller calls) ---
async function callClaude(system, userMsg) {
  const key = process.env.ANTHROPIC_API_KEY;
  const r = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01' },
    body: JSON.stringify({
      model: 'claude-sonnet-4-5-20250929', max_tokens: 8000,
      system, messages: [{ role: 'user', content: userMsg }],
    }),
  });
  const d = await r.json();
  if (d.error) throw new Error(d.error.message);
  return (d.content || []).filter(b => b.type === 'text').map(b => b.text).join('\n');
}

async function synthesizeContext(signals, amplitude) {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) { console.warn('[synth] No API key'); return {}; }

  const signalSummary = signals.slice(0, 40).map(s =>
    `[${s.source}] ${s.title || s.text?.slice(0, 100) || ''}`
  ).join('\n');

  const today = new Date().toISOString().slice(0, 10);

  // Call 1: Team + Cofounders
  let teamData = {};
  try {
    console.log('[synth] Generating team context...');
    const text = await callClaude(
      `Generate JSON for a product team dashboard. Team: ${JSON.stringify(TEAM)}. Cofounders: ${JSON.stringify(COFOUNDERS)}. Today: ${today}. Respond ONLY with valid JSON, no markdown:\n{"team":[{"name":"<n>","role":"<r>","squad":"<sq>","status":"shipping|attention|blocked","topConcern":"<1 sent>","linearActive":<n>,"linearBlocked":<n>,"slackLastSeen":"<ISO>","fourPAge":"<Nd>","meetingsToday":<n>}],"cofounders":[{"name":"<n>","role":"<r>","attention":"<1 sent>","recentTopics":["<t>"],"lastSlackToNoah":"<ISO>","pendingDecisions":["<item>"]}]}`,
      `Signals:\n${signalSummary}\n\nGenerate team and cofounder context.`
    );
    teamData = repairJSON(text) || {};
    console.log('[synth] ✓ team');
  } catch(e) { console.warn('[synth] ✗ team:', e.message); }

  // Call 2: Customers
  let custData = {};
  try {
    console.log('[synth] Generating customer context...');
    const text = await callClaude(
      `Generate JSON for customers of Sift (telemetry observability for aerospace/defense). Customers: ${JSON.stringify(CUSTOMERS)}. Today: ${today}. Respond ONLY with valid JSON, no markdown:\n{"customers":[{"name":"<n>","tier":"enterprise|growth|pilot","trajectory":"expanding|stable|at-risk|contracting","wau":<n>,"topSignal":"<1 sent>","features":["<f>"],"lastActivity":"<ISO>","openIssues":<n>}]}`,
      `Signals:\n${signalSummary}\n\nGenerate customer intelligence.`
    );
    custData = repairJSON(text) || {};
    console.log('[synth] ✓ customers');
  } catch(e) { console.warn('[synth] ✗ customers:', e.message); }

  // Call 3: Decisions + Strategy + Timeline
  let stratData = {};
  try {
    console.log('[synth] Generating strategy context...');
    const text = await callClaude(
      `Generate JSON for product strategy dashboard. Sift's 2026 strategy: Signal>Evidence>Decision. Pillars: Nail the Core, Embed Deeper, Build the Moat. North Star: Decisions Captured Per Customer. Key products: Explore V2, Canvas, Python Rules, Sift Edge, Ask SIFT. Today: ${today}. Respond ONLY with valid JSON, no markdown:\n{"decisions":[{"title":"<t>","context":"<why>","owner":"<who>","deadline":"<YYYY-MM-DD>","status":"open|blocked","blockedBy":"<what>","arguments":{"for":"<r>","against":"<r>"}}],"strategyMetrics":{"northStar":{"name":"Decisions Captured Per Customer","value":"<n>","delta":"<+/-%>"},"pillars":[{"name":"<p>","status":"on_track|at_risk|off_track","keyResults":[{"name":"<kr>","current":"<v>","target":"<v>","status":"on_track|at_risk"}]}]},"timeAudit":{"today":{"date":"${today}","meetings":5,"focusBlocks":2,"oneOnOnes":3,"freeHours":2,"meetingHours":6},"thisWeek":{"meetings":22,"freeHours":8,"meetingHours":32},"weekSummary":"<1 sent>","alerts":["<a>"]},"timeline":{"sections":[{"label":"<period>","events":[{"title":"<e>","date":"<YYYY-MM-DD>","time":"<HH:MM>","type":"deadline|gate|meeting|milestone","description":"<brief>","owner":"<who>"}]}]}}`,
      `Signals:\n${signalSummary}\n\nGenerate decisions, strategy metrics, time audit, and timeline.`
    );
    stratData = repairJSON(text) || {};
    console.log('[synth] ✓ strategy');
  } catch(e) { console.warn('[synth] ✗ strategy:', e.message); }

  return { ...teamData, ...custData, ...stratData };
}

// --- MAIN ---
async function main() {
  console.log(`[radar] Starting at ${new Date().toISOString()}`);

  const [amplitude, slackSignals, linearSignals] = await Promise.all([
    pullAmplitude(), pullSlack(), pullLinear(),
  ]);

  const allSignals = [...slackSignals, ...linearSignals];
  console.log(`[radar] ${allSignals.length} signals collected`);

  const context = await synthesizeContext(allSignals, amplitude);

  const data = {
    fetchedAt: new Date().toISOString(),
    _meta: {
      sources_scanned: [amplitude ? 'amplitude' : null, slackSignals.length ? 'slack' : null, linearSignals.length ? 'linear' : null].filter(Boolean).length,
      source_list: [amplitude ? 'amplitude' : null, slackSignals.length ? 'slack' : null, linearSignals.length ? 'linear' : null].filter(Boolean),
      signal_count: allSignals.length,
    },
    signals: allSignals,
    amplitude: amplitude || {},
    team: context.team || [],
    cofounders: context.cofounders || [],
    customers: context.customers || [],
    decisions: context.decisions || [],
    strategyMetrics: context.strategyMetrics || {},
    timeAudit: context.timeAudit || {},
    timeline: context.timeline || {},
    voc: { customers: [] },
  };

  const outPath = process.argv[2] || './data.json';
  fs.writeFileSync(outPath, JSON.stringify(data, null, 2));
  console.log(`[radar] ✓ Written to ${outPath} (${(JSON.stringify(data).length / 1024).toFixed(1)}KB)`);
}

main().catch(e => { console.error('[radar] Fatal:', e); process.exit(1); });
