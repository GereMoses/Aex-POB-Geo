import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Button, Input, Tooltip, Badge, Typography, Space, Switch, TimePicker, Popover, Tag } from 'antd';
import {
  CustomerServiceOutlined, SendOutlined, CloseOutlined,
  ThunderboltOutlined, ClearOutlined, CopyOutlined, CheckOutlined,
  DatabaseOutlined, LoadingOutlined, LeftOutlined, AppstoreOutlined,
  AudioOutlined, AudioMutedOutlined, DownloadOutlined, LinkOutlined,
  BellOutlined, BellFilled, SettingOutlined, ExclamationCircleFilled,
  WarningFilled, InfoCircleFilled,
} from '@ant-design/icons';
import {
  BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis,
  Tooltip as RTooltip, ResponsiveContainer, Legend,
} from 'recharts';
import dayjs from 'dayjs';
import { useTheme } from '../../contexts/ThemeContext';

const { Text } = Typography;

const STORAGE_KEY  = 'aria_chat_history';
const SCHEDULE_KEY = 'aria_briefing_schedule';

// ── Route map for actionable links ───────────────────────────────────────────
const TOOL_ROUTES = {
  get_onsite_personnel:     { label: 'View in Attendance', route: '/attendance' },
  get_attendance_summary:   { label: 'Open Attendance', route: '/attendance' },
  get_att_report:           { label: 'Open Attendance', route: '/attendance' },
  get_departments:          { label: 'Open Departments', route: '/departments' },
  get_positions:            { label: 'Open Positions', route: '/positions' },
  get_personnel_list:       { label: 'Open Personnel', route: '/personnel' },
  search_personnel:         { label: 'Open Personnel', route: '/personnel' },
  get_employment_contracts: { label: 'Open Contracts', route: '/personnel' },
  get_disciplinary:         { label: 'Open Disciplinary', route: '/personnel' },
  get_performance:          { label: 'Open Performance', route: '/personnel' },
  get_resignations:         { label: 'Open Resignations', route: '/personnel' },
  get_shifts:               { label: 'Open Schedules', route: '/attendance' },
  get_holidays:             { label: 'Open Calendar', route: '/attendance' },
  get_att_exceptions:       { label: 'Open Exceptions', route: '/attendance' },
  get_overtime:             { label: 'Open Overtime', route: '/attendance' },
  get_leave_requests:       { label: 'Open Leave', route: '/attendance/leave' },
  get_leave_balance:        { label: 'Open Leave Balance', route: '/attendance/leave' },
  get_expiring_items:       { label: 'Open Contractors', route: '/contractors' },
  get_contractor_status:    { label: 'Open Contractors', route: '/contractors' },
  get_visitor_summary:      { label: 'Open Visitors', route: '/visitors' },
  get_zones_summary:        { label: 'Open Warehouses', route: '/zones' },
  get_zones_detail:         { label: 'Open Warehouses', route: '/zones' },
  get_emergency_events:     { label: 'Open Emergency', route: '/emergency' },
  get_meeting_rooms:        { label: 'Open Meetings', route: '/meeting' },
  get_training:             { label: 'Open Training', route: '/personnel/training' },
  get_anomaly_alerts:       { label: 'Open Attendance', route: '/attendance' },
  get_notifications:        { label: 'Open Notifications', route: '/notifications' },
};

// ── Suggestion categories ─────────────────────────────────────────────────────
const SUGGESTION_CATEGORIES = [
  { label: '👥 Personnel', items: [
    { text: 'Who is on-site right now?',            icon: '👥' },
    { text: 'List all active employees',             icon: '📋' },
    { text: 'Show all departments',                  icon: '🏢' },
    { text: 'Show all positions',                    icon: '💼' },
    { text: 'Employment contracts',                  icon: '📄' },
    { text: 'Any resignations?',                     icon: '🚪' },
  ]},
  { label: '⏰ Attendance & Time', items: [
    { text: "Today's attendance summary",            icon: '📊' },
    { text: 'Attendance report last week',           icon: '📅' },
    { text: 'Compare this week vs last week',        icon: '↔️' },
    { text: 'Show all shifts',                       icon: '⏰' },
    { text: 'Upcoming holidays',                     icon: '🎉' },
    { text: 'Attendance exceptions',                 icon: '⚠️' },
    { text: 'Overtime records',                      icon: '⏱️' },
  ]},
  { label: '🗓️ Leave', items: [
    { text: 'Pending leave requests',                icon: '🗓️' },
    { text: 'Approved leave this month',             icon: '✅' },
    { text: 'Leave balances',                        icon: '📊' },
    { text: 'Compare leave this month vs last month',icon: '↔️' },
  ]},
  { label: '🛢️ POB & Ops', items: [
    { text: 'Generate a daily briefing',             icon: '📋' },
    { text: 'POB status',                            icon: '🛢️' },
    { text: 'Transport schedule',                    icon: '✈️' },
  ]},
  { label: '🔐 Security', items: [
    { text: 'Any security anomalies this week?',     icon: '🔍' },
    { text: 'Access levels',                         icon: '🔐' },
  ]},
  { label: '📡 Devices & Warehouses', items: [
    { text: 'How many readers are online?',          icon: '📡' },
    { text: 'Warehouse detail list',                      icon: '🗺️' },
    { text: 'Personnel areas',                       icon: '📍' },
  ]},
  { label: '🏗️ Compliance', items: [
    { text: 'Any contractors with expired permits?', icon: '⚠️' },
    { text: 'Medical clearance issues',              icon: '🏥' },
    { text: 'Training courses',                      icon: '🎓' },
    { text: 'Disciplinary cases',                    icon: '⚖️' },
    { text: 'Performance appraisals',                icon: '📈' },
  ]},
];
const INITIAL_SUGGESTIONS = SUGGESTION_CATEGORIES.flatMap(c => c.items).slice(0, 8);

// ── Markdown renderer (with full table support) ───────────────────────────────
function renderMarkdown(raw) {
  if (!raw) return '';
  let text = raw;

  // ── Tables: | Header | ... | \n |---|...| \n | row | ... |
  text = text.replace(
    /^\|(.+)\|\r?\n\|[-:| ]+\|\r?\n((?:\|.+\|\r?\n?)+)/gm,
    (_, headerLine, bodyLines) => {
      const escape = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      const parseRow = line => line.split('|').map(c => c.trim()).filter(Boolean);
      const headers = parseRow(headerLine);
      const rows = bodyLines.trim().split(/\r?\n/).map(parseRow);
      const th = headers.map(h => `<th>${escape(h.replace(/\*\*/g,''))}</th>`).join('');
      const trs = rows.map(row =>
        `<tr>${row.map(c => `<td>${escape(c.replace(/\*\*/g,''))}</td>`).join('')}</tr>`
      ).join('');
      return `<div class="aria-table-wrap"><table><thead><tr>${th}</tr></thead><tbody>${trs}</tbody></table></div>`;
    }
  );

  // ── Headings
  text = text
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm,  '<h2>$1</h2>')
    .replace(/^# (.+)$/gm,   '<h1>$1</h1>');

  // ── Inline
  text = text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,     '<em>$1</em>')
    .replace(/`([^`]+)`/g,     '<code>$1</code>');

  // ── Lists
  text = text
    .replace(/^[-•]\s(.+)/gm, '<li>$1</li>')
    .replace(/(<li>[\s\S]+?<\/li>)(\n<li>|$)/g, (m, li, next) =>
      next === '' ? `<ul>${li}</ul>` : `<ul>${li}</ul>` + next.trimStart()
    );
  // wrap consecutive <li>
  text = text.replace(/(<li>.*?<\/li>\n?)+/gs, m => `<ul>${m}</ul>`);

  // ── Paragraphs
  text = text.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br/>');

  return `<p>${text}</p>`;
}

const Markdown = ({ children }) => {
  if (!children) return null;
  return <div className="aria-md" dangerouslySetInnerHTML={{ __html: renderMarkdown(children) }} />;
};

// ── CSV export ────────────────────────────────────────────────────────────────
// Download an ARIA-generated PDF report. The /report endpoint is auth-gated, so a
// plain <a download> won't work — fetch with the token, then save the blob.
async function downloadReport(report) {
  if (!report?.url) return;
  try {
    const token = localStorage.getItem('token') || localStorage.getItem('authToken') || localStorage.getItem('access_token');
    const res = await fetch(report.url, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = report.filename || 'report.pdf';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  } catch (e) {
    console.error('ARIA report download failed', e);
  }
}

function exportCSV(text, filename = 'aria-report.csv') {
  const tableMatch = text.match(/\|(.+)\|\n\|[-| ]+\|\n([\s\S]+?)(?:\n\n|$)/);
  if (!tableMatch) {
    // No table — export raw text
    const blob = new Blob([text], { type: 'text/plain' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
    a.download = filename.replace('.csv', '.txt'); a.click(); return;
  }
  const headers = tableMatch[1].split('|').map(h => h.trim()).filter(Boolean);
  const rows = tableMatch[2].trim().split('\n').map(row =>
    row.split('|').map(c => c.trim().replace(/\*\*/g, '')).filter(Boolean)
  );
  const csv = [headers.join(','), ...rows.map(r => r.map(c => `"${c.replace(/"/g, '""')}"`).join(','))].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
  a.download = filename; a.click();
}

// ── Inline chart ──────────────────────────────────────────────────────────────
const CHART_COLORS = ['#10b981','#1677ff','#f59e0b','#8b5cf6','#ef4444','#06b6d4','#ec4899'];

const InlineChart = ({ chart, isDark }) => {
  if (!chart) return null;
  const bg   = isDark ? '#1a1a1a' : '#f8f9fa';
  const text = isDark ? '#aaa' : '#555';

  if (chart.chart_type === 'stat_group') {
    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, margin: '10px 0' }}>
        {chart.data.map((d, i) => (
          <div key={i} style={{
            background: isDark ? '#1e1e1e' : '#f0fdf4',
            border: `1px solid ${isDark ? '#2a2a2a' : '#d1fae5'}`,
            borderRadius: 10, padding: '8px 14px', textAlign: 'center', minWidth: 90,
          }}>
            <div style={{ fontSize: 22, fontWeight: 800, color: d.color }}>{d.value}</div>
            <div style={{ fontSize: 11, color: text }}>{d.label}</div>
          </div>
        ))}
      </div>
    );
  }

  if (chart.chart_type === 'bar') {
    const dataKey = chart.data[0] ? Object.keys(chart.data[0]).find(k => k !== 'dept' && k !== 'course') || 'value' : 'value';
    const xKey    = chart.data[0] ? ['dept', 'course', 'name'].find(k => k in (chart.data[0] || {})) || 'name' : 'name';
    return (
      <div style={{ background: bg, borderRadius: 10, padding: '12px 6px', margin: '10px 0' }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: text, marginBottom: 6, paddingLeft: 8 }}>{chart.title}</div>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={chart.data} margin={{ top: 4, right: 8, left: -20, bottom: 20 }}>
            <XAxis dataKey={xKey} tick={{ fill: text, fontSize: 10 }} angle={-30} textAnchor="end" interval={0} />
            <YAxis tick={{ fill: text, fontSize: 10 }} />
            <RTooltip contentStyle={{ background: isDark ? '#1e1e1e' : '#fff', border: '1px solid #2a2a2a', borderRadius: 8 }} />
            {(chart.keys || [{ key: dataKey, color: '#10b981', name: 'Value' }]).map(k => (
              <Bar key={k.key} dataKey={k.key} name={k.name} fill={k.color} radius={[4,4,0,0]} />
            ))}
            {chart.keys?.length > 1 && <Legend wrapperStyle={{ fontSize: 10, color: text }} />}
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (chart.chart_type === 'pie') {
    return (
      <div style={{ background: bg, borderRadius: 10, padding: '12px 6px', margin: '10px 0' }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: text, marginBottom: 4, paddingLeft: 8 }}>{chart.title}</div>
        <ResponsiveContainer width="100%" height={160}>
          <PieChart>
            <Pie data={chart.data} cx="50%" cy="50%" outerRadius={60} dataKey="value"
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              labelLine={false}>
              {chart.data.map((entry, i) => (
                <Cell key={i} fill={entry.color || CHART_COLORS[i % CHART_COLORS.length]} />
              ))}
            </Pie>
            <RTooltip contentStyle={{ background: isDark ? '#1e1e1e' : '#fff', border: '1px solid #333', borderRadius: 8 }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }
  return null;
};

// ── Typing dots ───────────────────────────────────────────────────────────────
const TypingDots = () => <span className="aria-typing"><span /><span /><span /></span>;

// ── Tool call card ────────────────────────────────────────────────────────────
const TOOL_LABELS = {
  get_dashboard_stats: 'Loading system overview…', get_onsite_personnel: 'Checking who is on-site…',
  get_expiring_items: 'Scanning compliance records…', get_contractor_status: 'Fetching contractor data…',
  get_attendance_summary: 'Pulling attendance records…', get_visitor_summary: 'Checking visitor logs…',
  get_anomaly_alerts: 'Scanning for anomalies…', search_personnel: 'Searching personnel…',
  get_leave_requests: 'Fetching leave requests…', get_pob_status: 'Getting POB status…',
  get_zones_summary: 'Loading warehouse data…', get_departments: 'Loading departments…',
  get_shifts: 'Loading shifts…', get_training: 'Loading training data…',
};
const ToolCard = ({ tool, isDark }) => (
  <div style={{
    display: 'inline-flex', alignItems: 'center', gap: 7,
    padding: '5px 12px', borderRadius: 20, marginBottom: 6, marginRight: 6,
    background: isDark ? 'rgba(16,185,129,0.1)' : 'rgba(16,185,129,0.07)',
    border: `1px solid ${isDark ? 'rgba(16,185,129,0.25)' : 'rgba(16,185,129,0.2)'}`,
    fontSize: 12,
  }}>
    <LoadingOutlined style={{ color: '#10b981', fontSize: 11 }} spin />
    <DatabaseOutlined style={{ color: '#10b981', fontSize: 11 }} />
    <span style={{ color: isDark ? '#6ee7b7' : '#059669' }}>{TOOL_LABELS[tool] || `Running ${tool}…`}</span>
  </div>
);

// ── Copy button ───────────────────────────────────────────────────────────────
const CopyBtn = ({ text, isDark }) => {
  const [copied, setCopied] = useState(false);
  return (
    <button onClick={() => { navigator.clipboard.writeText(text).then(() => { setCopied(true); setTimeout(() => setCopied(false), 2000); }); }}
      style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '3px 6px', borderRadius: 5, color: isDark ? '#555' : '#bbb', transition: 'all 0.15s' }}
      onMouseEnter={e => e.currentTarget.style.color = '#10b981'}
      onMouseLeave={e => e.currentTarget.style.color = isDark ? '#555' : '#bbb'}>
      {copied ? <CheckOutlined style={{ fontSize: 12, color: '#10b981' }} /> : <CopyOutlined style={{ fontSize: 12 }} />}
    </button>
  );
};

// ── Message bubble ────────────────────────────────────────────────────────────
const Bubble = ({ msg, isDark, onFollowUp, onNavigate }) => {
  const isUser   = msg.role === 'user';
  const isSystem = msg.role === 'system';
  if (isSystem) return (
    <div style={{ textAlign: 'center', padding: '6px 0', fontSize: 12, color: isDark ? '#444' : '#ccc', fontStyle: 'italic' }}>{msg.content}</div>
  );
  const routeInfo = msg.toolsUsed?.length === 1 ? TOOL_ROUTES[msg.toolsUsed[0]] : null;
  return (
    <div style={{ display: 'flex', flexDirection: isUser ? 'row-reverse' : 'row', gap: 12, marginBottom: 20, alignItems: 'flex-end' }}>
      <div style={{
        width: 34, height: 34, borderRadius: 11, flexShrink: 0,
        background: isUser ? 'linear-gradient(135deg, #1677ff, #0958d9)' : 'linear-gradient(135deg, #10b981, #059669)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 15, color: '#fff', fontWeight: 700, boxShadow: '0 2px 10px rgba(0,0,0,0.15)',
      }}>
        {isUser ? 'U' : <CustomerServiceOutlined />}
      </div>
      <div style={{ maxWidth: '82%', display: 'flex', flexDirection: 'column', alignItems: isUser ? 'flex-end' : 'flex-start' }}>
        {!isUser && msg.toolCalls?.length > 0 && (
          <div style={{ marginBottom: 6 }}>
            {msg.toolCalls.map((t, i) => <ToolCard key={i} tool={t} isDark={isDark} />)}
          </div>
        )}
        <div style={{
          background: isUser ? 'linear-gradient(135deg, #1677ff, #0958d9)' : isDark ? '#1e1e1e' : '#f5f6f7',
          color: isUser ? '#fff' : isDark ? '#e0e0e0' : '#1a1a1a',
          borderRadius: isUser ? '18px 18px 4px 18px' : '4px 18px 18px 18px',
          padding: '12px 16px', fontSize: 14, lineHeight: 1.65,
          boxShadow: isDark ? '0 2px 8px rgba(0,0,0,0.3)' : '0 2px 8px rgba(0,0,0,0.07)',
          border: isUser ? 'none' : `1px solid ${isDark ? '#2a2a2a' : '#ececec'}`,
          maxWidth: '100%', overflow: 'hidden',
        }}>
          {msg.streaming && !msg.content
            ? <TypingDots />
            : <>
                <Markdown>{msg.content}</Markdown>
                {msg.chartData && (
                  <div style={{ marginTop: 12, borderTop: `1px solid ${isDark ? '#2a2a2a' : '#e8e8e8'}`, paddingTop: 12 }}>
                    <InlineChart chart={msg.chartData} isDark={isDark} />
                  </div>
                )}
                {msg.report && (
                  <div style={{ marginTop: 12 }}>
                    <button onClick={() => downloadReport(msg.report)}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: '#10b981', color: '#fff', border: 'none', borderRadius: 8, padding: '8px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer', boxShadow: '0 2px 6px rgba(16,185,129,0.3)' }}
                      onMouseEnter={e => e.currentTarget.style.background = '#059669'}
                      onMouseLeave={e => e.currentTarget.style.background = '#10b981'}>
                      <DownloadOutlined /> {msg.report.label || 'Download report (PDF)'}
                    </button>
                  </div>
                )}
              </>
          }
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 5, padding: '0 4px', flexDirection: isUser ? 'row-reverse' : 'row', flexWrap: 'wrap' }}>
          <span style={{ fontSize: 11, color: isDark ? '#3a3a3a' : '#ccc' }}>
            {dayjs(msg.ts).format('HH:mm')}{msg.provider && ` · ${msg.provider}`}
          </span>
          {!isUser && msg.content && <CopyBtn text={msg.content} isDark={isDark} />}
          {!isUser && msg.content && (
            <button onClick={() => exportCSV(msg.content)} title="Download CSV"
              style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '3px 6px', borderRadius: 5, color: isDark ? '#555' : '#bbb', transition: 'all 0.15s', fontSize: 12 }}
              onMouseEnter={e => e.currentTarget.style.color = '#10b981'}
              onMouseLeave={e => e.currentTarget.style.color = isDark ? '#555' : '#bbb'}>
              <DownloadOutlined />
            </button>
          )}
          {routeInfo && (
            <button onClick={() => onNavigate(routeInfo.route)}
              style={{ background: 'none', border: `1px solid ${isDark ? '#333' : '#e0e0e0'}`, cursor: 'pointer', padding: '2px 8px', borderRadius: 10, color: isDark ? '#555' : '#888', fontSize: 11, display: 'flex', alignItems: 'center', gap: 4, transition: 'all 0.15s' }}
              onMouseEnter={e => { e.currentTarget.style.color = '#10b981'; e.currentTarget.style.borderColor = '#10b981'; }}
              onMouseLeave={e => { e.currentTarget.style.color = isDark ? '#555' : '#888'; e.currentTarget.style.borderColor = isDark ? '#333' : '#e0e0e0'; }}>
              <LinkOutlined /> {routeInfo.label}
            </button>
          )}
        </div>
        {!isUser && msg.followUps?.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
            {msg.followUps.map(s => (
              <button key={s} onClick={() => onFollowUp(s)} style={{
                border: `1px solid ${isDark ? 'rgba(16,185,129,0.2)' : 'rgba(16,185,129,0.25)'}`,
                borderRadius: 20, padding: '4px 12px', fontSize: 12, cursor: 'pointer',
                background: isDark ? 'rgba(16,185,129,0.07)' : 'rgba(16,185,129,0.05)',
                color: isDark ? '#6ee7b7' : '#059669', transition: 'all 0.15s',
              }}
              onMouseEnter={e => e.currentTarget.style.background = isDark ? 'rgba(16,185,129,0.15)' : 'rgba(16,185,129,0.1)'}
              onMouseLeave={e => e.currentTarget.style.background = isDark ? 'rgba(16,185,129,0.07)' : 'rgba(16,185,129,0.05)'}>
                ↳ {s}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// ── Alert icon by level ───────────────────────────────────────────────────────
const AlertIcon = ({ level }) => {
  if (level === 'critical') return <ExclamationCircleFilled style={{ color: '#ef4444' }} />;
  if (level === 'warning')  return <WarningFilled style={{ color: '#f59e0b' }} />;
  return <InfoCircleFilled style={{ color: '#1677ff' }} />;
};

// ── Schedule settings popover ─────────────────────────────────────────────────
const ScheduleSettings = ({ isDark }) => {
  const saved = JSON.parse(localStorage.getItem(SCHEDULE_KEY) || '{}');
  const [enabled, setEnabled] = useState(saved.enabled || false);
  const [time,    setTime]    = useState(saved.time || '07:00');

  const save = (en, t) => {
    const s = { enabled: en, time: t };
    localStorage.setItem(SCHEDULE_KEY, JSON.stringify(s));
    setEnabled(en); setTime(t);
  };

  return (
    <div style={{ width: 240, padding: 4 }}>
      <div style={{ fontWeight: 700, marginBottom: 12, color: isDark ? '#e0e0e0' : '#1a1a1a' }}>Scheduled Briefing</div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <Text style={{ fontSize: 13 }}>Enable daily briefing</Text>
        <Switch size="small" checked={enabled} onChange={v => save(v, time)} style={{ background: enabled ? '#10b981' : undefined }} />
      </div>
      {enabled && (
        <div>
          <Text style={{ fontSize: 12, color: isDark ? '#777' : '#888', display: 'block', marginBottom: 6 }}>Briefing time</Text>
          <TimePicker
            format="HH:mm" size="small" style={{ width: '100%' }}
            defaultValue={dayjs(time, 'HH:mm')}
            onChange={(_, s) => save(enabled, s)}
          />
          <div style={{ marginTop: 8, fontSize: 11, color: isDark ? '#555' : '#aaa' }}>
            ARIA will auto-run the daily briefing at this time.
          </div>
        </div>
      )}
    </div>
  );
};

// ── Main Widget ───────────────────────────────────────────────────────────────
const ARIAWidget = () => {
  const { isDark } = useTheme();

  // Core state
  const [open,             setOpen]             = useState(false);
  const [input,            setInput]            = useState('');
  const [messages,         setMessages]         = useState(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); } catch { return []; }
  });
  const [loading,          setLoading]          = useState(false);
  const [provider,         setProvider]         = useState(null);
  const [unread,           setUnread]           = useState(0);

  // Feature state
  const [showQuickActions, setShowQuickActions] = useState(false);
  const [qaCategory,       setQaCategory]       = useState(null);
  const [alerts,           setAlerts]           = useState([]);
  const [alertBanner,      setAlertBanner]      = useState(null);
  const [listening,        setListening]        = useState(false);
  const [scheduleOpen,     setScheduleOpen]     = useState(false);

  const bottomRef  = useRef(null);
  const inputRef   = useRef(null);
  const speechRef  = useRef(null);
  const alertTimer = useRef(null);

  // ── 1. Chat persistence ───────────────────────────────────────────────────
  useEffect(() => {
    const toSave = messages.slice(-50).map(m => ({ ...m, streaming: false }));
    localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
  }, [messages]);

  // ── 2. Keyboard shortcut Ctrl+K / Cmd+K ──────────────────────────────────
  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setOpen(o => { if (!o) setTimeout(() => inputRef.current?.focus(), 200); return !o; });
        setShowQuickActions(false);
      }
      if (e.key === 'Escape' && open) setOpen(false);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open]);

  // ── 5. Proactive alerts polling ───────────────────────────────────────────
  useEffect(() => {
    const poll = async () => {
      try {
        const token = localStorage.getItem('token') || localStorage.getItem('authToken') || localStorage.getItem('access_token');
        const res = await fetch('/api/v1/ai/alerts', { headers: token ? { Authorization: `Bearer ${token}` } : {} });
        if (res.ok) {
          const data = await res.json();
          setAlerts(data.alerts || []);
          if (!open && data.count > 0) setUnread(u => Math.max(u, data.count));
          // Show top critical alert as banner
          const crit = (data.alerts || []).find(a => a.level === 'critical');
          if (crit) setAlertBanner(crit);
        }
      } catch (_) {}
    };
    poll();
    const interval = setInterval(poll, 60000);
    return () => clearInterval(interval);
  }, [open]);

  // ── 10. Scheduled briefing check ─────────────────────────────────────────
  useEffect(() => {
    const check = () => {
      try {
        const sched = JSON.parse(localStorage.getItem(SCHEDULE_KEY) || '{}');
        if (!sched.enabled || !sched.time) return;
        const [hh, mm] = sched.time.split(':').map(Number);
        const now = new Date();
        if (now.getHours() === hh && now.getMinutes() === mm) {
          setOpen(true);
          setTimeout(() => sendMessage("Generate today's full operations briefing"), 500);
        }
      } catch (_) {}
    };
    alertTimer.current = setInterval(check, 60000);
    return () => clearInterval(alertTimer.current);
  }, []);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);
  useEffect(() => {
    if (open) { setUnread(0); setTimeout(() => inputRef.current?.focus(), 200); }
  }, [open]);
  useEffect(() => {
    if (open && messages.length === 0) {
      setMessages([{
        role: 'assistant',
        content: "👋 Hi, I'm **ARIA** — your AI Operations Assistant.\n\nI have live access to your Apex POB. Ask me anything, or pick a quick action below.",
        ts: Date.now(), toolCalls: [],
      }]);
    }
  }, [open]);

  // ── 7. Voice input ────────────────────────────────────────────────────────
  const startVoice = useCallback(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { alert('Voice input is not supported in this browser.'); return; }
    const rec = new SR();
    rec.lang = 'en-US'; rec.interimResults = false; rec.maxAlternatives = 1;
    rec.onresult  = (e) => { setInput(e.results[0][0].transcript); setListening(false); };
    rec.onend     = () => setListening(false);
    rec.onerror   = () => setListening(false);
    speechRef.current = rec;
    rec.start(); setListening(true);
  }, []);

  const stopVoice = useCallback(() => {
    speechRef.current?.stop(); setListening(false);
  }, []);

  // ── Send message ──────────────────────────────────────────────────────────
  const sendMessage = useCallback(async (text) => {
    const q = (text ?? input).trim();
    if (!q || loading) return;
    setInput('');
    setShowQuickActions(false);

    const userMsg      = { role: 'user',      content: q, ts: Date.now() };
    const assistantMsg = { role: 'assistant', content: '', ts: Date.now(), streaming: true, toolCalls: [], chartData: null, followUps: [], toolsUsed: [] };

    setMessages(prev => [...prev, userMsg, assistantMsg]);
    setLoading(true);

    const history = [...messages, userMsg].map(m => ({ role: m.role, content: m.content }));

    try {
      const token = localStorage.getItem('token') || localStorage.getItem('authToken') || localStorage.getItem('access_token');
      const response = await fetch('/api/v1/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ messages: history }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let localProvider = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const evt = JSON.parse(line.slice(6));
            if (evt.type === 'provider') {
              localProvider = evt.info?.provider ?? null; setProvider(localProvider);
            } else if (evt.type === 'tool_call') {
              setMessages(prev => { const n=[...prev]; const l={...n[n.length-1]}; if(!l.toolCalls.includes(evt.tool)) l.toolCalls=[...l.toolCalls,evt.tool]; n[n.length-1]=l; return n; });
            } else if (evt.type === 'chart_data') {
              setMessages(prev => { const n=[...prev]; const l={...n[n.length-1]}; l.chartData=evt.chart; n[n.length-1]=l; return n; });
            } else if (evt.type === 'report') {
              setMessages(prev => { const n=[...prev]; const l={...n[n.length-1]}; l.report={ url: evt.url, filename: evt.filename, label: evt.label }; n[n.length-1]=l; return n; });
            } else if (evt.type === 'text') {
              setMessages(prev => { const n=[...prev]; const l={...n[n.length-1]}; l.content=(l.content??'')+evt.text; l.streaming=false; n[n.length-1]=l; return n; });
            } else if (evt.type === 'follow_ups') {
              setMessages(prev => { const n=[...prev]; const l={...n[n.length-1]}; l.followUps=evt.items||[]; n[n.length-1]=l; return n; });
            } else if (evt.type === 'done') {
              setMessages(prev => {
                const n=[...prev]; const l={...n[n.length-1]};
                l.streaming=false; l.provider=localProvider;
                l.toolsUsed=[...l.toolCalls]; n[n.length-1]=l; return n;
              });
            } else if (evt.type === 'error') {
              setMessages(prev => { const n=[...prev]; const l={...n[n.length-1]}; l.content=`⚠️ ${evt.text}`; l.streaming=false; n[n.length-1]=l; return n; });
            }
          } catch (_) {}
        }
      }
    } catch (err) {
      setMessages(prev => { const n=[...prev]; const l={...n[n.length-1]}; l.content=`⚠️ Could not reach ARIA: ${err.message}`; l.streaming=false; n[n.length-1]=l; return n; });
    } finally {
      setLoading(false);
      if (!open) setUnread(u => u + 1);
    }
  }, [input, loading, messages, open]);

  const handleKeyDown = e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } };

  const handleNavigate = (route) => {
    window.location.hash = route;
    setOpen(false);
  };

  // ── Trigger tab ───────────────────────────────────────────────────────────
  return (
    <>
      {/* Backdrop */}
      <div onClick={() => setOpen(false)} style={{
        position: 'fixed', inset: 0, zIndex: 1198,
        background: 'rgba(0,0,0,0.25)', opacity: open ? 1 : 0,
        pointerEvents: open ? 'all' : 'none', transition: 'opacity 0.2s ease',
      }} />

      {/* Panel */}
      <div style={{
        position: 'fixed', top: 0, right: 0, width: 660, height: '100vh', zIndex: 1199,
        transform: open ? 'translateX(0)' : 'translateX(100%)',
        transition: 'transform 0.2s ease',
        display: 'flex', flexDirection: 'column',
        background: isDark ? '#0f0f0f' : '#ffffff',
        boxShadow: '-4px 0 20px rgba(0,0,0,0.2)',
        borderLeft: `1px solid ${isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'}`,
      }}>

        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 14, padding: '16px 20px',
          background: 'linear-gradient(135deg, #047857 0%, #10b981 60%, #0d9488 100%)', flexShrink: 0,
        }}>
          <div style={{ width: 42, height: 42, borderRadius: 13, background: 'rgba(255,255,255,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <CustomerServiceOutlined style={{ fontSize: 22, color: '#fff' }} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ color: '#fff', fontWeight: 800, fontSize: 18, letterSpacing: 0.5 }}>ARIA</div>
            <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: 11, display: 'flex', alignItems: 'center', gap: 6, marginTop: 1 }}>
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#a7f3d0', boxShadow: '0 0 8px #6ee7b7', display: 'inline-block' }} />
              {provider ?? 'AI Operations Assistant'}
              <span style={{ opacity: 0.5 }}>· No limits · Private</span>
              <Tag style={{ fontSize: 9, padding: '0 5px', marginLeft: 2, borderRadius: 8, background: 'rgba(255,255,255,0.12)', border: 'none', color: 'rgba(255,255,255,0.7)' }}>
                Ctrl+K
              </Tag>
            </div>
          </div>
          <Space size={2}>
            <Tooltip title="Quick Actions"><Button type="text" size="small" icon={<AppstoreOutlined />}
              style={{ color: showQuickActions ? '#fff' : 'rgba(255,255,255,0.9)', borderRadius: 8, height: 32, width: 32, background: showQuickActions ? 'rgba(255,255,255,0.2)' : 'transparent' }}
              onClick={() => { setShowQuickActions(q => !q); setQaCategory(null); }} /></Tooltip>
            <Tooltip title="Daily Briefing"><Button type="text" size="small" icon={<ThunderboltOutlined />}
              style={{ color: 'rgba(255,255,255,0.9)', borderRadius: 8, height: 32, width: 32 }}
              onClick={() => { setShowQuickActions(false); sendMessage("Generate today's full operations briefing"); }} /></Tooltip>
            {/* Notification bell — always visible; badge + amber only when alerts exist */}
            <Tooltip title={alerts.length > 0 ? `${alerts.length} alert(s)` : 'Notifications & alerts'}>
              <Badge count={alerts.length} size="small" offset={[2, -2]}>
                <Button type="text" size="small" icon={alerts.length > 0 ? <BellFilled /> : <BellOutlined />}
                  style={{ color: alerts.length > 0 ? '#fbbf24' : 'rgba(255,255,255,0.9)', borderRadius: 8, height: 32, width: 32 }}
                  onClick={() => sendMessage('Show system notifications and alerts')} />
              </Badge>
            </Tooltip>
            {/* Settings — Button must be the Popover's DIRECT child or the click
                trigger gets swallowed by a wrapping Tooltip and never toggles. */}
            <Popover content={<ScheduleSettings isDark={isDark} />} trigger="click" open={scheduleOpen} onOpenChange={setScheduleOpen} placement="bottomRight">
              <Button type="text" size="small" icon={<SettingOutlined />} title="Schedule Briefing"
                style={{ color: 'rgba(255,255,255,0.9)', borderRadius: 8, height: 32, width: 32 }} />
            </Popover>
            <Tooltip title="Clear chat"><Button type="text" size="small" icon={<ClearOutlined />}
              style={{ color: 'rgba(255,255,255,0.9)', borderRadius: 8, height: 32, width: 32 }}
              onClick={() => { setMessages([]); setShowQuickActions(false); localStorage.removeItem(STORAGE_KEY); }} /></Tooltip>
            <Button type="text" size="small" icon={<CloseOutlined />}
              style={{ color: '#fff', borderRadius: 8, height: 32, width: 32, background: 'rgba(255,255,255,0.12)' }}
              onClick={() => setOpen(false)} />
          </Space>
        </div>

        {/* Critical alert banner */}
        {alertBanner && (
          <div style={{
            background: '#7f1d1d', color: '#fecaca', padding: '8px 16px', fontSize: 12,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0,
          }}>
            <span>🚨 {alertBanner.msg}</span>
            <button onClick={() => setAlertBanner(null)}
              style={{ background: 'none', border: 'none', color: '#fecaca', cursor: 'pointer', fontSize: 16, lineHeight: 1 }}>×</button>
          </div>
        )}

        {/* Messages area */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px 12px', position: 'relative', scrollbarWidth: 'thin', scrollbarColor: isDark ? '#2a2a2a transparent' : '#e5e5e5 transparent' }}>

          {/* Quick Actions overlay */}
          {showQuickActions && (
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, background: isDark ? '#0f0f0f' : '#fff', zIndex: 10, overflowY: 'auto', padding: '16px 20px' }}>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, color: isDark ? '#444' : '#bbb', textTransform: 'uppercase', marginBottom: 14 }}>Quick Actions</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
                {[{ label: 'All', val: null }, ...SUGGESTION_CATEGORIES.map(c => ({ label: c.label, val: c.label }))].map(({ label, val }) => (
                  <button key={label} onClick={() => setQaCategory(val)}
                    style={{ border: `1px solid ${qaCategory === val ? '#10b981' : (isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)')}`, borderRadius: 16, padding: '4px 12px', fontSize: 11, cursor: 'pointer', background: qaCategory === val ? 'rgba(16,185,129,0.1)' : 'transparent', color: qaCategory === val ? '#10b981' : (isDark ? '#666' : '#888'), fontWeight: qaCategory === val ? 700 : 400 }}>
                    {label}
                  </button>
                ))}
              </div>
              {(qaCategory ? SUGGESTION_CATEGORIES.filter(c => c.label === qaCategory) : SUGGESTION_CATEGORIES).map(cat => (
                <div key={cat.label} style={{ marginBottom: 18 }}>
                  <div style={{ fontSize: 11, color: isDark ? '#555' : '#aaa', fontWeight: 600, marginBottom: 8 }}>{cat.label}</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>
                    {cat.items.map(s => (
                      <button key={s.text} onClick={() => { sendMessage(s.text); setShowQuickActions(false); }}
                        style={{ display: 'flex', alignItems: 'center', gap: 6, border: `1px solid ${isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'}`, borderRadius: 20, padding: '6px 13px', fontSize: 12.5, cursor: 'pointer', background: isDark ? 'rgba(255,255,255,0.03)' : '#fafafa', color: isDark ? '#888' : '#555', transition: 'all 0.15s' }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor='#10b981'; e.currentTarget.style.color='#10b981'; e.currentTarget.style.background=isDark?'rgba(16,185,129,0.1)':'rgba(16,185,129,0.06)'; }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor=isDark?'rgba(255,255,255,0.08)':'rgba(0,0,0,0.08)'; e.currentTarget.style.color=isDark?'#888':'#555'; e.currentTarget.style.background=isDark?'rgba(255,255,255,0.03)':'#fafafa'; }}>
                        <span>{s.icon}</span><span>{s.text}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {messages.map((m, i) => (
            <Bubble key={i} msg={m} isDark={isDark}
              onFollowUp={t => { setShowQuickActions(false); sendMessage(t); }}
              onNavigate={handleNavigate} />
          ))}

          {/* Initial suggestion chips */}
          {messages.length === 1 && !showQuickActions && (
            <div style={{ marginTop: 4 }}>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, color: isDark ? '#444' : '#bbb', textTransform: 'uppercase', marginBottom: 12 }}>Quick actions</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {INITIAL_SUGGESTIONS.map(s => (
                  <button key={s.text} onClick={() => sendMessage(s.text)}
                    style={{ display: 'flex', alignItems: 'center', gap: 6, border: `1px solid ${isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'}`, borderRadius: 22, padding: '7px 14px', fontSize: 13, cursor: 'pointer', background: isDark ? 'rgba(255,255,255,0.03)' : '#fafafa', color: isDark ? '#777' : '#555', transition: 'all 0.15s' }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor='#10b981'; e.currentTarget.style.color='#10b981'; e.currentTarget.style.background=isDark?'rgba(16,185,129,0.1)':'rgba(16,185,129,0.06)'; }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor=isDark?'rgba(255,255,255,0.08)':'rgba(0,0,0,0.08)'; e.currentTarget.style.color=isDark?'#777':'#555'; e.currentTarget.style.background=isDark?'rgba(255,255,255,0.03)':'#fafafa'; }}>
                    <span style={{ fontSize: 15 }}>{s.icon}</span><span>{s.text}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input area */}
        <div style={{ padding: '12px 20px 16px', borderTop: `1px solid ${isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'}`, background: isDark ? 'rgba(255,255,255,0.015)' : 'rgba(0,0,0,0.01)', flexShrink: 0 }}>
          <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', background: isDark ? '#1a1a1a' : '#f5f5f5', borderRadius: 16, border: `1.5px solid ${isDark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.07)'}`, padding: '8px 8px 8px 16px', transition: 'border-color 0.2s' }}
            onFocusCapture={e => e.currentTarget.style.borderColor='#10b981'}
            onBlurCapture={e => e.currentTarget.style.borderColor=isDark?'rgba(255,255,255,0.07)':'rgba(0,0,0,0.07)'}>
            <Input.TextArea ref={inputRef} value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown}
              placeholder="Ask anything… or try 'compare this week vs last week'" autoSize={{ minRows: 1, maxRows: 5 }}
              disabled={loading} variant="borderless"
              style={{ fontSize: 14, resize: 'none', padding: 0, background: 'transparent', color: isDark ? '#e0e0e0' : '#1a1a1a' }} />
            {/* Voice button */}
            <Tooltip title={listening ? 'Stop listening' : 'Voice input'}>
              <Button type="text" shape="circle" size="small"
                icon={listening ? <AudioMutedOutlined style={{ color: '#ef4444' }} /> : <AudioOutlined />}
                onClick={listening ? stopVoice : startVoice}
                style={{ color: listening ? '#ef4444' : (isDark ? '#555' : '#aaa'), flexShrink: 0, width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', background: listening ? 'rgba(239,68,68,0.1)' : 'transparent' }} />
            </Tooltip>
            <Button type="primary" shape="circle"
              icon={loading ? <LoadingOutlined /> : <SendOutlined />}
              onClick={() => sendMessage()} disabled={loading || !input.trim()}
              style={{ background: input.trim() && !loading ? '#10b981' : undefined, borderColor: input.trim() && !loading ? '#10b981' : undefined, flexShrink: 0, width: 38, height: 38, minWidth: 38, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 15 }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8, padding: '0 2px' }}>
            <Text style={{ fontSize: 10, color: isDark ? '#2e2e2e' : '#ccc' }}>Enter · Shift+Enter new line · Ctrl+K toggle</Text>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#10b981', boxShadow: '0 0 6px #10b981', display: 'inline-block' }} />
              <Text style={{ fontSize: 11, color: '#10b981', fontWeight: 500 }}>{provider ?? 'Connecting…'}</Text>
            </div>
          </div>
        </div>
      </div>

      {/* Trigger tab */}
      <div onClick={() => { setOpen(o => !o); setShowQuickActions(false); }}
        style={{ position: 'fixed', right: open ? 660 : 0, top: '50%', transform: 'translateY(-50%)', zIndex: 1200, cursor: 'pointer', transition: 'right 0.2s ease' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 6, width: 48, padding: '18px 0', borderRadius: '12px 0 0 12px', background: open ? 'linear-gradient(180deg, #047857, #059669)' : 'linear-gradient(180deg, #10b981, #059669)', boxShadow: open ? '-4px 0 20px rgba(5,150,105,0.5)' : '-4px 0 20px rgba(16,185,129,0.4)', color: '#fff', transition: 'background 0.2s' }}>
          {open ? <LeftOutlined style={{ fontSize: 16 }} /> : (
            <>
              <Badge count={unread} size="small" offset={[8, -4]}>
                <CustomerServiceOutlined style={{ fontSize: 20, color: '#fff' }} />
              </Badge>
              <div style={{ writingMode: 'vertical-rl', textOrientation: 'mixed', transform: 'rotate(180deg)', fontSize: 11, fontWeight: 700, letterSpacing: 2, color: 'rgba(255,255,255,0.9)', marginTop: 4 }}>ARIA</div>
            </>
          )}
          {alerts.length > 0 && !open && (
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#f59e0b', marginTop: 2 }} />
          )}
        </div>
      </div>

      {/* Styles */}
      <style>{`
        .aria-md p{margin:0 0 8px}.aria-md p:last-child{margin-bottom:0}
        .aria-md ul{margin:6px 0 6px 20px;padding:0}.aria-md li{margin-bottom:4px}
        .aria-md strong{font-weight:700}.aria-md em{font-style:italic}
        .aria-md h1,.aria-md h2,.aria-md h3{margin:12px 0 6px;font-size:15px;font-weight:700}
        .aria-md code{background:rgba(16,185,129,0.12);border-radius:5px;padding:2px 6px;font-size:13px;font-family:monospace;color:#10b981}
        .aria-table-wrap{overflow-x:auto;margin:10px 0;border-radius:8px;border:1px solid rgba(16,185,129,0.2)}
        .aria-table-wrap table{border-collapse:collapse;width:100%;font-size:12.5px;min-width:300px}
        .aria-table-wrap thead tr{background:rgba(16,185,129,0.12)}
        .aria-table-wrap th{padding:8px 12px;text-align:left;font-weight:700;color:#10b981;white-space:nowrap;border-bottom:2px solid rgba(16,185,129,0.25)}
        .aria-table-wrap td{padding:7px 12px;border-bottom:1px solid rgba(128,128,128,0.1);vertical-align:top}
        .aria-table-wrap tbody tr:hover{background:rgba(16,185,129,0.05)}
        .aria-table-wrap tbody tr:last-child td{border-bottom:none}
        .aria-typing{display:inline-flex;gap:5px;align-items:center;padding:4px 0}
        .aria-typing span{width:8px;height:8px;border-radius:50%;background:#10b981;display:inline-block;animation:ariaBounce 1.2s infinite ease-in-out}
        .aria-typing span:nth-child(2){animation-delay:0.2s}
        .aria-typing span:nth-child(3){animation-delay:0.4s}
        @keyframes ariaBounce{0%,80%,100%{transform:scale(0.55);opacity:0.4}40%{transform:scale(1);opacity:1}}
      `}</style>
    </>
  );
};

export default ARIAWidget;
