import React, { useState, useMemo } from 'react';
import {
  Table, Card, Button, Space, Tag, App, Form, Drawer, Input,
  InputNumber, Row, Col, Divider, Descriptions, Tooltip, Badge,
  Statistic, Switch, TimePicker, Select, Popconfirm, Popover,
  Segmented, Dropdown, Empty,
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined,
  ReloadOutlined, ClockCircleOutlined, SearchOutlined, SettingOutlined,
  CheckCircleOutlined, CopyOutlined, DownloadOutlined, DownOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../../../services/api';
import dayjs from 'dayjs';
import { fmtT, toMin, ColTogglePopover } from './shared';

const { Option } = Select;

/* ─── 24-h time bar — break shows as white gap ──────────────────────────── */
const TimetableBar = ({ start, end, breakStart, breakEnd, color = '#1890ff', height = 8 }) => {
  const s = toMin(start);
  const e = toMin(end);
  if (!start || !end) return null;
  const night    = e > 0 && e < s;
  const leftPct  = (s / 1440) * 100;
  const widthPct = night ? ((1440 - s + e) / 1440) * 100 : Math.max(((e - s) / 1440) * 100, 1);
  const bs = toMin(breakStart);
  const be = toMin(breakEnd);
  const hasBreak = breakStart && breakEnd && be > bs;
  return (
    <div style={{ position: 'relative', height, background: '#f0f0f0', borderRadius: height / 2, overflow: 'visible' }}>
      <div style={{
        position: 'absolute', left: `${leftPct}%`, width: `${widthPct}%`,
        height: '100%', background: color, borderRadius: height / 2, minWidth: 4,
      }} />
      {hasBreak && (
        <div style={{
          position: 'absolute',
          left: `${(bs / 1440) * 100}%`, width: `${Math.max(((be - bs) / 1440) * 100, 0.5)}%`,
          height: '100%', background: '#fff', borderRadius: 2, opacity: 0.75, zIndex: 1,
        }} />
      )}
      {[0, 25, 50, 75].map(p => (
        <div key={p} style={{ position: 'absolute', left: `${p}%`, top: -2, width: 1, height: height + 4, background: '#e0e0e0' }} />
      ))}
    </div>
  );
};

/* ─── Net work hours (shift duration minus break) ───────────────────────── */
const netHours = (checkin, checkout, breakStart, breakEnd) => {
  if (!checkin || !checkout) return null;
  const s = toMin(checkin);
  const e = toMin(checkout);
  const isNight  = e > 0 && e < s;
  const shiftMin = isNight ? (1440 - s + e) : (e - s);
  const bs = toMin(breakStart);
  const be = toMin(breakEnd);
  const breakMin = breakStart && breakEnd && be > bs ? (be - bs) : 0;
  return ((shiftMin - breakMin) / 60).toFixed(1);
};

/* ─── Preset shift templates ─────────────────────────────────────────────── */
const PRESET_TEMPLATES = [
  { label: 'Morning  07:00 – 16:00', alias: 'Morning 07:00–16:00',  checkin: '07:00:00', checkout: '16:00:00', breakStart: '12:00:00', breakEnd: '13:00:00' },
  { label: 'Morning  08:00 – 17:00', alias: 'Morning 08:00–17:00',  checkin: '08:00:00', checkout: '17:00:00', breakStart: '12:00:00', breakEnd: '13:00:00' },
  { label: 'Afternoon 14:00 – 22:00', alias: 'Afternoon 14:00–22:00', checkin: '14:00:00', checkout: '22:00:00' },
  { label: 'Night  22:00 – 06:00',   alias: 'Night 22:00–06:00',    checkin: '22:00:00', checkout: '06:00:00' },
  { label: 'Half Day AM  08:00 – 12:00', alias: 'Half Day AM',     checkin: '08:00:00', checkout: '12:00:00', work_day: 0.5 },
  { label: 'Half Day PM  13:00 – 17:00', alias: 'Half Day PM',     checkin: '13:00:00', checkout: '17:00:00', work_day: 0.5 },
];

/* ─── Quick filter chips ─────────────────────────────────────────────────── */
const CHIP_FILTERS = [
  { key: 'has-break',  label: 'Has Break',       test: r => !!r.break_time_start },
  { key: 'night',      label: 'Night Shift',      test: r => { const s = toMin(r.checkin_time), e = toMin(r.checkout_time); return r.checkin_time && r.checkout_time && e > 0 && e < s; } },
  { key: 'full-day',   label: 'Full Day (1.0×)',  test: r => (r.work_day ?? 1) === 1.0 },
  { key: 'half-day',   label: 'Half Day (0.5×)',  test: r => r.work_day === 0.5 },
  { key: 'in-use',     label: 'In Use',           test: r => (r.shift_count ?? 0) > 0 },
];

/* ─────────────────────────────────────────────────────────────────────────── */

const TimetablesTab = () => {
  const { message, modal } = App.useApp();
  const qc = useQueryClient();

  const [search,          setSearch]          = useState('');
  const [statusFilter,    setStatusFilter]    = useState('active');
  const [tagFilters,      setTagFilters]      = useState(new Set());
  const [drawerOpen,      setDrawerOpen]      = useState(false);
  const [detailOpen,      setDetailOpen]      = useState(false);
  const [editing,         setEditing]         = useState(null);
  const [detailRec,       setDetailRec]       = useState(null);
  const [hiddenCols,      setHiddenCols]      = useState(new Set(['updated']));
  const [colPopOpen,      setColPopOpen]      = useState(false);
  const [preview,         setPreview]         = useState({});
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [bulkLoading,     setBulkLoading]     = useState(false);
  const [form] = Form.useForm();

  /* ── T&A Areas (personnel_area — Lagos Area, Abuja Office, etc.) ─────────── */
  const { data: areasRaw } = useQuery({
    queryKey: ['ta-areas'],
    // Warehouses replaced the old device areas as the location filter.
    queryFn: () => apiService.get('/api/v1/zones/dashboard'),
    staleTime: 120000,
  });
  const areas = useMemo(() => {
    const r = areasRaw?.data || areasRaw?.results || areasRaw || [];
    return Array.isArray(r) ? r : [];
  }, [areasRaw]);

  /* ── Timetables ──────────────────────────────────────────────────────────── */
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['att-timetables'],
    queryFn: () => apiService.get('/api/v1/attendance/timetables'),
    refetchInterval: 60000,
  });
  const allRows = useMemo(() => {
    const r = data?.data || data || [];
    return Array.isArray(r) ? r : [];
  }, [data]);

  const rows = useMemo(() => {
    let r = allRows;
    if (statusFilter === 'active')   r = r.filter(x => x.is_active !== false);
    if (statusFilter === 'inactive') r = r.filter(x => x.is_active === false);
    if (search) {
      const q = search.toLowerCase();
      r = r.filter(x => (x.alias || '').toLowerCase().includes(q));
    }
    CHIP_FILTERS.forEach(f => { if (tagFilters.has(f.key)) r = r.filter(f.test); });
    return r;
  }, [allRows, search, statusFilter, tagFilters]);

  /* ── Stats ───────────────────────────────────────────────────────────────── */
  const activeCount    = allRows.filter(r => r.is_active !== false).length;
  const withBreakCount = allRows.filter(r => r.break_time_start).length;
  const nightCount     = allRows.filter(r => {
    const s = toMin(r.checkin_time), e = toMin(r.checkout_time);
    return r.checkin_time && r.checkout_time && e > 0 && e < s;
  }).length;
  const avgHours = useMemo(() => {
    const hrs = allRows
      .filter(r => r.is_active !== false)
      .map(r => parseFloat(netHours(r.checkin_time, r.checkout_time, r.break_time_start, r.break_time_end)))
      .filter(h => !isNaN(h) && h > 0);
    return hrs.length ? (hrs.reduce((a, b) => a + b, 0) / hrs.length).toFixed(1) : null;
  }, [allRows]);

  /* ── Mutations ───────────────────────────────────────────────────────────── */
  const saveM = useMutation({
    mutationFn: (d) => editing
      ? apiService.put(`/api/v1/attendance/timetables/${editing.id}`, d)
      : apiService.post('/api/v1/attendance/timetables', d),
    onSuccess: () => {
      message.success(editing ? 'Timetable updated' : 'Timetable created');
      closeDrawer();
      qc.invalidateQueries(['att-timetables']);
    },
    onError: (e) => message.error(e?.message || 'Failed to save timetable'),
  });

  const deleteM = useMutation({
    mutationFn: (id) => apiService.delete(`/api/v1/attendance/timetables/${id}`),
    onSuccess: () => {
      message.success('Timetable deleted');
      qc.invalidateQueries(['att-timetables']);
    },
    onError: (e) => message.error(e?.message || 'Failed to delete timetable'),
  });

  const toggleStatusM = useMutation({
    mutationFn: ({ id, is_active }) =>
      apiService.patch(`/api/v1/attendance/timetables/${id}/status`, { is_active }),
    onSuccess: () => qc.invalidateQueries(['att-timetables']),
    onError: () => message.error('Failed to update status'),
  });

  /* ── Bulk operations ─────────────────────────────────────────────────────── */
  const bulkSetActive = async (is_active) => {
    setBulkLoading(true);
    try {
      await Promise.all(
        selectedRowKeys.map(id => apiService.patch(`/api/v1/attendance/timetables/${id}/status`, { is_active }))
      );
      const n = selectedRowKeys.length;
      message.success(`${is_active ? 'Activated' : 'Deactivated'} ${n} timetable${n > 1 ? 's' : ''}`);
      setSelectedRowKeys([]);
      qc.invalidateQueries(['att-timetables']);
    } catch {
      message.error('Some updates failed');
    } finally {
      setBulkLoading(false);
    }
  };

  const bulkDelete = async () => {
    setBulkLoading(true);
    try {
      await Promise.all(selectedRowKeys.map(id => apiService.delete(`/api/v1/attendance/timetables/${id}`)));
      const n = selectedRowKeys.length;
      message.success(`Deleted ${n} timetable${n > 1 ? 's' : ''}`);
      setSelectedRowKeys([]);
      qc.invalidateQueries(['att-timetables']);
    } catch {
      message.error('Some deletions failed');
    } finally {
      setBulkLoading(false);
    }
  };

  /* ── Export CSV ──────────────────────────────────────────────────────────── */
  const exportCSV = () => {
    const headers = ['Name', 'Check-in', 'Check-out', 'Net Hours', 'Break Start', 'Break End',
      'Break (min)', 'Late Grace (min)', 'Early Grace (min)', 'Work Day', 'Shifts Used', 'Area', 'Status'];
    const body = rows.map(r => [
      `"${(r.alias || '').replace(/"/g, '""')}"`,
      fmtT(r.checkin_time), fmtT(r.checkout_time),
      netHours(r.checkin_time, r.checkout_time, r.break_time_start, r.break_time_end) || '',
      r.break_time_start ? fmtT(r.break_time_start) : '',
      r.break_time_end   ? fmtT(r.break_time_end)   : '',
      r.break_time_start && r.break_time_end ? toMin(r.break_time_end) - toMin(r.break_time_start) : '',
      r.late_minutes  ?? 0,
      r.early_minutes ?? 0,
      r.work_day ?? 1.0,
      r.shift_count ?? 0,
      `"${(r.area_name || '').replace(/"/g, '""')}"`,
      r.is_active !== false ? 'Active' : 'Inactive',
    ]);
    const csv = [headers, ...body].map(row => row.join(',')).join('\n');
    const a = Object.assign(document.createElement('a'), {
      href: URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' })),
      download: `timetables_${dayjs().format('YYYY-MM-DD')}.csv`,
    });
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  /* ── Drawer helpers ──────────────────────────────────────────────────────── */
  const fillForm = (vals, pvw) => {
    setTimeout(() => { form.resetFields(); form.setFieldsValue(vals); setPreview(pvw); }, 0);
  };

  const openDrawer = (rec = null, duplicate = false) => {
    setEditing(duplicate ? null : rec);
    setDrawerOpen(true);
    if (rec) {
      fillForm({
        ...rec,
        alias:            duplicate ? `${rec.alias} (copy)` : rec.alias,
        checkin_time:     rec.checkin_time     ? dayjs(rec.checkin_time,     'HH:mm:ss') : null,
        checkout_time:    rec.checkout_time    ? dayjs(rec.checkout_time,    'HH:mm:ss') : null,
        break_time_start: rec.break_time_start ? dayjs(rec.break_time_start, 'HH:mm:ss') : null,
        break_time_end:   rec.break_time_end   ? dayjs(rec.break_time_end,   'HH:mm:ss') : null,
        late_minutes:  rec.late_minutes  ?? 0,
        early_minutes: rec.early_minutes ?? 0,
        work_day:      rec.work_day      ?? 1.0,
        must_checkin:  rec.must_checkin  ?? true,
        must_checkout: rec.must_checkout ?? true,
        is_active:     duplicate ? true : (rec.is_active ?? true),
        color:         rec.color || '#1890ff',
      }, {
        checkin: rec.checkin_time, checkout: rec.checkout_time,
        breakStart: rec.break_time_start, breakEnd: rec.break_time_end,
        color: rec.color || '#1890ff',
      });
    } else {
      setTimeout(() => { form.resetFields(); setPreview({}); }, 0);
    }
  };

  const openFromTemplate = (t) => {
    setEditing(null);
    setDrawerOpen(true);
    fillForm({
      alias: t.alias,
      checkin_time:     dayjs(t.checkin,    'HH:mm:ss'),
      checkout_time:    dayjs(t.checkout,   'HH:mm:ss'),
      break_time_start: t.breakStart ? dayjs(t.breakStart, 'HH:mm:ss') : null,
      break_time_end:   t.breakEnd   ? dayjs(t.breakEnd,   'HH:mm:ss') : null,
      late_minutes: 15, early_minutes: 15,
      work_day: t.work_day ?? 1.0,
      must_checkin: true, must_checkout: true, is_active: true,
      color: '#1890ff',
    }, {
      checkin: t.checkin, checkout: t.checkout,
      breakStart: t.breakStart, breakEnd: t.breakEnd, color: '#1890ff',
    });
  };

  const closeDrawer = () => { setDrawerOpen(false); form.resetFields(); setEditing(null); setPreview({}); };

  const handleValuesChange = (_, all) => {
    setPreview({
      checkin:    all.checkin_time?.format('HH:mm:ss'),
      checkout:   all.checkout_time?.format('HH:mm:ss'),
      breakStart: all.break_time_start?.format('HH:mm:ss'),
      breakEnd:   all.break_time_end?.format('HH:mm:ss'),
      color:      all.color || '#1890ff',
    });
  };

  const submit = () => form.validateFields().then(v =>
    saveM.mutate({
      alias:            v.alias,
      checkin_time:     v.checkin_time?.format('HH:mm:ss')     ?? null,
      checkout_time:    v.checkout_time?.format('HH:mm:ss')    ?? null,
      late_minutes:     v.late_minutes  ?? 0,
      early_minutes:    v.early_minutes ?? 0,
      work_day:         v.work_day      ?? 1.0,
      color:            v.color         || '#1890ff',
      break_time_start: v.break_time_start?.format('HH:mm:ss') ?? null,
      break_time_end:   v.break_time_end?.format('HH:mm:ss')   ?? null,
      must_checkin:     v.must_checkin  ?? true,
      must_checkout:    v.must_checkout ?? true,
      area_id:          v.area_id       ?? null,
      is_active:        v.is_active     ?? true,
    })
  ).catch(() => {});

  const toggleCol = (key) => setHiddenCols(prev => {
    const n = new Set(prev); n.has(key) ? n.delete(key) : n.add(key); return n;
  });

  const toggleTag = (key) => setTagFilters(prev => {
    const n = new Set(prev); n.has(key) ? n.delete(key) : n.add(key); return n;
  });

  /* ── Column definitions ──────────────────────────────────────────────────── */
  const COL_DEFS = [
    {
      title: 'Name', key: 'alias',
      sorter: (a, b) => (a.alias || '').localeCompare(b.alias || ''),
      render: (_, r) => (
        <button type="button"
          style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer', textAlign: 'left' }}
          onClick={() => { setDetailRec(r); setDetailOpen(true); }}>
          <Space size={10}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: r.color || '#1890ff', flexShrink: 0 }} />
            <Space direction="vertical" size={0}>
              <span style={{ fontWeight: 700, fontSize: 13, color: '#1890ff' }}>{r.alias}</span>
              {r.area_name && <span style={{ fontSize: 11, color: '#8c8c8c' }}>{r.area_name}</span>}
            </Space>
          </Space>
        </button>
      ),
    },
    {
      title: 'Time Window', key: 'time', width: 220,
      render: (_, r) => {
        const s = toMin(r.checkin_time), e = toMin(r.checkout_time);
        const isNight = r.checkin_time && r.checkout_time && e > 0 && e < s;
        const net = netHours(r.checkin_time, r.checkout_time, r.break_time_start, r.break_time_end);
        return (
          <div>
            <Space style={{ marginBottom: 5 }} size={4} wrap>
              <span style={{ fontWeight: 700 }}>{fmtT(r.checkin_time)}</span>
              <span style={{ color: '#bfbfbf' }}>→</span>
              <span style={{ fontWeight: 700 }}>{fmtT(r.checkout_time)}</span>
              {isNight && <Tag color="purple" style={{ margin: 0, fontSize: 11 }}>Night</Tag>}
              {net    && <Tag color="blue"   style={{ margin: 0, fontSize: 11 }}>{net}h</Tag>}
            </Space>
            <TimetableBar
              start={r.checkin_time} end={r.checkout_time}
              breakStart={r.break_time_start} breakEnd={r.break_time_end}
              color={r.color || '#1890ff'}
            />
          </div>
        );
      },
    },
    {
      title: 'Grace Periods', key: 'grace', width: 150,
      render: (_, r) => (
        <Space direction="vertical" size={3}>
          <Space size={5}>
            <Tag color="green" style={{ fontSize: 11, margin: 0 }}>Late</Tag>
            <span style={{ fontSize: 12, fontWeight: 600 }}>{r.late_minutes ?? 0} min</span>
          </Space>
          <Space size={5}>
            <Tag color="orange" style={{ fontSize: 11, margin: 0 }}>Early</Tag>
            <span style={{ fontSize: 12, fontWeight: 600 }}>{r.early_minutes ?? 0} min</span>
          </Space>
        </Space>
      ),
    },
    {
      title: 'Break', key: 'break', width: 130,
      render: (_, r) => r.break_time_start ? (
        <Space direction="vertical" size={0}>
          <span style={{ fontSize: 12, fontWeight: 600 }}>{fmtT(r.break_time_start)} – {fmtT(r.break_time_end)}</span>
          <span style={{ fontSize: 11, color: '#8c8c8c' }}>
            {toMin(r.break_time_end) - toMin(r.break_time_start)} min
          </span>
        </Space>
      ) : <span style={{ color: '#bfbfbf', fontSize: 12 }}>No break</span>,
    },
    {
      title: 'Work Day', key: 'workday', dataIndex: 'work_day', width: 88, align: 'center',
      sorter: (a, b) => (a.work_day ?? 1) - (b.work_day ?? 1),
      render: v => <Tag color="cyan">{v ?? 1.0}×</Tag>,
    },
    {
      title: 'Shifts', key: 'shifts', dataIndex: 'shift_count', width: 72, align: 'center',
      sorter: (a, b) => (a.shift_count ?? 0) - (b.shift_count ?? 0),
      render: v => (v ?? 0) > 0
        ? <Badge count={v} style={{ backgroundColor: '#1890ff' }} />
        : <span style={{ color: '#d9d9d9', fontSize: 12 }}>—</span>,
    },
    {
      title: 'Status', key: 'status', dataIndex: 'is_active', width: 110,
      sorter: (a, b) => (b.is_active === false ? 0 : 1) - (a.is_active === false ? 0 : 1),
      render: (v, r) => (
        <Space size={6}>
          <Switch
            size="small"
            checked={v !== false}
            loading={toggleStatusM.isPending && toggleStatusM.variables?.id === r.id}
            onChange={(checked) => toggleStatusM.mutate({ id: r.id, is_active: checked })}
          />
          <span style={{ fontSize: 12, color: v !== false ? '#52c41a' : '#8c8c8c' }}>
            {v !== false ? 'Active' : 'Inactive'}
          </span>
        </Space>
      ),
    },
    {
      title: 'Updated', key: 'updated', dataIndex: 'updated_at', width: 100,
      sorter: (a, b) => new Date(a.updated_at || 0) - new Date(b.updated_at || 0),
      render: v => v
        ? <span style={{ fontSize: 11, color: '#8c8c8c' }}>{dayjs(v).format('MMM D, YYYY')}</span>
        : '—',
    },
  ];

  const cols = useMemo(() => {
    const visible = COL_DEFS.filter(c => !hiddenCols.has(c.key));
    return [...visible, {
      title: 'Actions', key: 'act', fixed: 'right', width: 148,
      render: (_, r) => (
        <Space size={4}>
          <Tooltip title="View details">
            <Button size="small" icon={<EyeOutlined />}
              onClick={() => { setDetailRec(r); setDetailOpen(true); }} />
          </Tooltip>
          <Tooltip title="Edit">
            <Button size="small" icon={<EditOutlined />} onClick={() => openDrawer(r)} />
          </Tooltip>
          <Tooltip title="Duplicate">
            <Button size="small" icon={<CopyOutlined />} onClick={() => openDrawer(r, true)} />
          </Tooltip>
          <Popconfirm
            title="Delete timetable?"
            description={
              (r.shift_count ?? 0) > 0
                ? `${r.shift_count} shift${r.shift_count > 1 ? 's' : ''} reference this timetable and will lose it.`
                : 'This action cannot be undone.'
            }
            onConfirm={() => deleteM.mutate(r.id)}
            okText="Delete" okButtonProps={{ danger: true }}>
            <Tooltip title="Delete">
              <Button size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    }];
  }, [hiddenCols, toggleStatusM.isPending, toggleStatusM.variables]);

  /* ── Form preview values ─────────────────────────────────────────────────── */
  const previewNet     = netHours(preview.checkin, preview.checkout, preview.breakStart, preview.breakEnd);
  const previewIsNight = preview.checkin && preview.checkout
    && toMin(preview.checkout) > 0 && toMin(preview.checkout) < toMin(preview.checkin);

  /* ── Add dropdown items ──────────────────────────────────────────────────── */
  const addMenuItems = [
    { key: 'blank', label: 'Blank timetable', icon: <PlusOutlined />, onClick: () => openDrawer() },
    { type: 'divider' },
    { key: 'grp', type: 'group', label: 'From preset' },
    ...PRESET_TEMPLATES.map((t, i) => ({ key: `pre-${i}`, label: t.label, onClick: () => openFromTemplate(t) })),
  ];

  /* ── Expandable row detail ───────────────────────────────────────────────── */
  const expandedRowRender = (r) => {
    const net = netHours(r.checkin_time, r.checkout_time, r.break_time_start, r.break_time_end);
    const isNight = r.checkin_time && r.checkout_time
      && toMin(r.checkout_time) > 0 && toMin(r.checkout_time) < toMin(r.checkin_time);
    const breakMin = r.break_time_start && r.break_time_end
      ? toMin(r.break_time_end) - toMin(r.break_time_start) : 0;
    return (
      <div style={{ padding: '12px 48px 16px', background: '#fafafa', borderTop: '1px solid #f0f0f0' }}>
        <Row gutter={32} align="top">
          <Col xs={24} md={10}>
            <TimetableBar
              start={r.checkin_time} end={r.checkout_time}
              breakStart={r.break_time_start} breakEnd={r.break_time_end}
              color={r.color || '#1890ff'} height={10}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#bfbfbf', marginTop: 3 }}>
              <span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>24:00</span>
            </div>
            <Space size={6} style={{ marginTop: 8 }} wrap>
              {net      && <Tag color="blue"   style={{ fontSize: 11 }}>{net}h net</Tag>}
              {isNight  && <Tag color="purple" style={{ fontSize: 11 }}>Night shift</Tag>}
              {breakMin > 0 && <Tag color="orange" style={{ fontSize: 11 }}>{breakMin} min break</Tag>}
            </Space>
          </Col>
          <Col xs={12} md={7}>
            <div style={{ fontSize: 11, color: '#8c8c8c', marginBottom: 6, fontWeight: 600 }}>Grace Periods</div>
            <Space direction="vertical" size={4}>
              <Space size={6}><Tag color="green" style={{ fontSize: 11, margin: 0 }}>Late</Tag><span style={{ fontSize: 12 }}>{r.late_minutes ?? 0} min</span></Space>
              <Space size={6}><Tag color="orange" style={{ fontSize: 11, margin: 0 }}>Early</Tag><span style={{ fontSize: 12 }}>{r.early_minutes ?? 0} min</span></Space>
            </Space>
          </Col>
          <Col xs={12} md={7}>
            <div style={{ fontSize: 11, color: '#8c8c8c', marginBottom: 6, fontWeight: 600 }}>Flags</div>
            <Space direction="vertical" size={4}>
              <Space size={6}>
                <Badge status={r.must_checkin  ? 'success' : 'default'} />
                <span style={{ fontSize: 12 }}>Must check-in: {r.must_checkin  ? 'Yes' : 'No'}</span>
              </Space>
              <Space size={6}>
                <Badge status={r.must_checkout ? 'success' : 'default'} />
                <span style={{ fontSize: 12 }}>Must check-out: {r.must_checkout ? 'Yes' : 'No'}</span>
              </Space>
              {(r.shift_count ?? 0) > 0 && (
                <Space size={6}>
                  <Badge count={r.shift_count} style={{ backgroundColor: '#1890ff' }} />
                  <span style={{ fontSize: 12 }}>shift{r.shift_count > 1 ? 's' : ''} using this</span>
                </Space>
              )}
            </Space>
          </Col>
        </Row>
      </div>
    );
  };

  /* ── Render ──────────────────────────────────────────────────────────────── */
  return (
    <div style={{ padding: 24 }}>

      {/* Stats */}
      <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
        {[
          { title: 'Total',          value: allRows.length,  icon: <ClockCircleOutlined />, color: '#1890ff' },
          { title: 'Active',         value: activeCount,     icon: <CheckCircleOutlined />, color: '#52c41a' },
          { title: 'With Break',     value: withBreakCount,  icon: <ClockCircleOutlined />, color: '#fa8c16' },
          { title: 'Avg Work Hours', value: avgHours || '—', icon: <ClockCircleOutlined />, color: '#722ed1',
            suffix: avgHours ? 'h' : '' },
        ].map(s => (
          <Col xs={12} sm={6} key={s.title}>
            <Card styles={{ body: { padding: '14px 18px' } }} style={{ borderTop: `3px solid ${s.color}` }}>
              <Statistic title={s.title} value={s.value} prefix={s.icon} suffix={s.suffix}
                valueStyle={{ color: s.color, fontSize: 24 }} />
            </Card>
          </Col>
        ))}
      </Row>

      {/* Toolbar */}
      <Card styles={{ body: { padding: '12px 16px' } }} style={{ marginBottom: 16 }}>
        <Row gutter={[12, 8]} align="middle" wrap>
          <Col xs={24} sm={10} md={7}>
            <Input placeholder="Search timetables…" prefix={<SearchOutlined />}
              value={search} onChange={e => setSearch(e.target.value)} allowClear />
          </Col>
          <Col>
            <Segmented
              value={statusFilter} onChange={setStatusFilter} size="middle"
              options={[
                { label: `All (${allRows.length})`,                    value: 'all'      },
                { label: `Active (${activeCount})`,                    value: 'active'   },
                { label: `Inactive (${allRows.length - activeCount})`, value: 'inactive' },
              ]}
            />
          </Col>
          <Col flex="auto" style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Space>
              <Dropdown menu={{ items: addMenuItems }} trigger={['click']}>
                <Button type="primary" icon={<PlusOutlined />}>
                  Add Timetable <DownOutlined style={{ fontSize: 11 }} />
                </Button>
              </Dropdown>
              <Tooltip title={`Export ${rows.length} row${rows.length !== 1 ? 's' : ''} to CSV`}>
                <Button icon={<DownloadOutlined />} onClick={exportCSV} disabled={!rows.length}>
                  Export
                </Button>
              </Tooltip>
              <Button icon={<ReloadOutlined />} onClick={() => refetch()} loading={isLoading}>
                Refresh
              </Button>
              <Popover
                title="Show / Hide Columns" trigger="click"
                open={colPopOpen} onOpenChange={setColPopOpen}
                content={<ColTogglePopover colDefs={COL_DEFS} hidden={hiddenCols} onToggle={toggleCol} />}>
                <Tooltip title="Adjust columns">
                  <Button icon={<SettingOutlined />} />
                </Tooltip>
              </Popover>
            </Space>
          </Col>
        </Row>

        {/* Filter chips */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
          {CHIP_FILTERS.map(f => (
            <Tag.CheckableTag
              key={f.key}
              checked={tagFilters.has(f.key)}
              onChange={() => toggleTag(f.key)}
              style={{ cursor: 'pointer', borderRadius: 12, fontSize: 12 }}
            >
              {f.label}
            </Tag.CheckableTag>
          ))}
          {tagFilters.size > 0 && (
            <Button
              size="small" type="link" style={{ padding: '0 4px', height: 22, fontSize: 12 }}
              onClick={() => setTagFilters(new Set())}>
              Clear filters
            </Button>
          )}
        </div>
      </Card>

      {/* Bulk action bar */}
      {selectedRowKeys.length > 0 && (
        <div style={{
          background: '#e6f4ff', border: '1px solid #91caff', borderRadius: 6,
          padding: '8px 16px', marginBottom: 8,
          display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap',
        }}>
          <span style={{ fontWeight: 600, fontSize: 13, color: '#0958d9' }}>
            {selectedRowKeys.length} selected
          </span>
          <Button size="small" onClick={() => bulkSetActive(true)} loading={bulkLoading}>
            Activate
          </Button>
          <Button size="small" onClick={() => bulkSetActive(false)} loading={bulkLoading}>
            Deactivate
          </Button>
          <Popconfirm
            title={`Delete ${selectedRowKeys.length} timetable${selectedRowKeys.length > 1 ? 's' : ''}?`}
            description="Shifts referencing these timetables will lose the reference."
            onConfirm={bulkDelete}
            okText="Delete All" okButtonProps={{ danger: true }}>
            <Button size="small" danger loading={bulkLoading}>Delete</Button>
          </Popconfirm>
          <Button size="small" type="link" style={{ paddingLeft: 0 }}
            onClick={() => setSelectedRowKeys([])}>
            Clear selection
          </Button>
        </div>
      )}

      {/* Table */}
      <Card styles={{ body: { padding: 0 } }}>
        <Table
          columns={cols}
          dataSource={rows}
          loading={isLoading}
          rowKey="id"
          size="middle"
          scroll={{ x: 1000 }}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (t, r) => `${r[0]}–${r[1]} of ${t}`,
          }}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
            getCheckboxProps: r => ({ name: r.alias }),
          }}
          expandable={{
            expandedRowRender,
            rowExpandable: () => true,
          }}
          onRow={r => ({ style: { opacity: r.is_active === false ? 0.55 : 1 } })}
          locale={{
            emptyText: (
              <div style={{ padding: 40 }}>
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description={
                    search || tagFilters.size > 0
                      ? 'No timetables match the current filters'
                      : statusFilter === 'inactive'
                        ? 'No inactive timetables'
                        : 'No timetables yet'
                  }
                >
                  {!search && tagFilters.size === 0 && statusFilter !== 'inactive' && (
                    <Dropdown menu={{ items: addMenuItems }} trigger={['click']}>
                      <Button type="primary" icon={<PlusOutlined />}>
                        Add First Timetable <DownOutlined style={{ fontSize: 11 }} />
                      </Button>
                    </Dropdown>
                  )}
                </Empty>
              </div>
            ),
          }}
        />
      </Card>

      {/* ── Detail Drawer ──────────────────────────────────────────────────── */}
      <Drawer
        title={<Space><EyeOutlined />Timetable Details</Space>}
        open={detailOpen} onClose={() => setDetailOpen(false)} width={460} destroyOnHidden
        extra={
          <Space>
            <Button size="small" icon={<CopyOutlined />}
              onClick={() => { setDetailOpen(false); openDrawer(detailRec, true); }}>
              Duplicate
            </Button>
            <Button size="small" icon={<EditOutlined />}
              onClick={() => { setDetailOpen(false); openDrawer(detailRec); }}>
              Edit
            </Button>
          </Space>
        }
      >
        {detailRec && (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
              <div style={{ width: 16, height: 16, borderRadius: '50%', background: detailRec.color || '#1890ff' }} />
              <span style={{ fontSize: 18, fontWeight: 700 }}>{detailRec.alias}</span>
              {(() => {
                const s = toMin(detailRec.checkin_time), e = toMin(detailRec.checkout_time);
                return detailRec.checkin_time && detailRec.checkout_time && e > 0 && e < s
                  ? <Tag color="purple">Night</Tag> : null;
              })()}
              <Badge
                status={detailRec.is_active !== false ? 'success' : 'default'}
                text={detailRec.is_active !== false ? 'Active' : 'Inactive'}
              />
            </div>

            <div style={{ marginBottom: 16 }}>
              <TimetableBar
                start={detailRec.checkin_time} end={detailRec.checkout_time}
                breakStart={detailRec.break_time_start} breakEnd={detailRec.break_time_end}
                color={detailRec.color || '#1890ff'} height={10}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#8c8c8c', marginTop: 4 }}>
                <span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>24:00</span>
              </div>
              {netHours(detailRec.checkin_time, detailRec.checkout_time, detailRec.break_time_start, detailRec.break_time_end) && (
                <div style={{ display: 'flex', gap: 8, marginTop: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
                  <Tag color="blue" style={{ fontSize: 12 }}>
                    {netHours(detailRec.checkin_time, detailRec.checkout_time, detailRec.break_time_start, detailRec.break_time_end)}h net work
                  </Tag>
                  {detailRec.break_time_start && detailRec.break_time_end && (
                    <Tag color="orange" style={{ fontSize: 12 }}>
                      {toMin(detailRec.break_time_end) - toMin(detailRec.break_time_start)} min break
                    </Tag>
                  )}
                  {(detailRec.shift_count ?? 0) > 0 && (
                    <Tag color="geekblue" style={{ fontSize: 12 }}>
                      {detailRec.shift_count} shift{detailRec.shift_count > 1 ? 's' : ''} assigned
                    </Tag>
                  )}
                </div>
              )}
            </div>

            <Divider orientation="left" style={{ fontSize: 12 }}>Schedule</Divider>
            <Descriptions column={2} size="small" bordered>
              <Descriptions.Item label="Check-in">{fmtT(detailRec.checkin_time)}</Descriptions.Item>
              <Descriptions.Item label="Check-out">{fmtT(detailRec.checkout_time)}</Descriptions.Item>
              <Descriptions.Item label="Late Grace">{detailRec.late_minutes ?? 0} min</Descriptions.Item>
              <Descriptions.Item label="Early Exit">{detailRec.early_minutes ?? 0} min</Descriptions.Item>
              <Descriptions.Item label="Work Day">{detailRec.work_day ?? 1.0}×</Descriptions.Item>
              <Descriptions.Item label="Area">{detailRec.area_name || '—'}</Descriptions.Item>
            </Descriptions>

            {detailRec.break_time_start && (
              <>
                <Divider orientation="left" style={{ fontSize: 12, marginTop: 14 }}>Break</Divider>
                <Descriptions column={2} size="small" bordered>
                  <Descriptions.Item label="Start">{fmtT(detailRec.break_time_start)}</Descriptions.Item>
                  <Descriptions.Item label="End">{fmtT(detailRec.break_time_end)}</Descriptions.Item>
                  <Descriptions.Item label="Duration" span={2}>
                    {toMin(detailRec.break_time_end) - toMin(detailRec.break_time_start)} min
                  </Descriptions.Item>
                </Descriptions>
              </>
            )}

            <Divider orientation="left" style={{ fontSize: 12, marginTop: 14 }}>Flags</Divider>
            <Descriptions column={2} size="small" bordered>
              <Descriptions.Item label="Must Check-in">
                <Badge status={detailRec.must_checkin  ? 'success' : 'default'} text={detailRec.must_checkin  ? 'Yes' : 'No'} />
              </Descriptions.Item>
              <Descriptions.Item label="Must Check-out">
                <Badge status={detailRec.must_checkout ? 'success' : 'default'} text={detailRec.must_checkout ? 'Yes' : 'No'} />
              </Descriptions.Item>
            </Descriptions>
          </>
        )}
      </Drawer>

      {/* ── Add / Edit Drawer ──────────────────────────────────────────────── */}
      <Drawer
        title={
          <Space>
            <ClockCircleOutlined style={{ color: '#1890ff' }} />
            {editing ? `Edit — ${editing.alias}` : 'Add Timetable'}
          </Space>
        }
        open={drawerOpen} onClose={closeDrawer} width={600} destroyOnHidden
        footer={
          <Space style={{ float: 'right' }}>
            <Button onClick={closeDrawer}>Cancel</Button>
            <Button type="primary" onClick={submit} loading={saveM.isPending}>
              {editing ? 'Update' : 'Create'}
            </Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical" size="small" onValuesChange={handleValuesChange}>
          <Divider orientation="left"><Space><ClockCircleOutlined />Identity</Space></Divider>
          <Row gutter={12}>
            <Col span={16}>
              <Form.Item name="alias" label="Name *" rules={[{ required: true, message: 'Name is required' }]}>
                <Input placeholder="e.g., Morning 08:00–17:00" size="middle" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="work_day" label="Work Day Value" initialValue={1.0}
                tooltip="1.0 = full day, 0.5 = half day">
                <Space.Compact style={{ width: '100%' }}><InputNumber min={0} max={2} step={0.5} size="middle" style={{ flex: 1 }} /><Input readOnly value="×" style={{ width: 36, textAlign: 'center' }} size="middle" /></Space.Compact>
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left"><Space><ClockCircleOutlined />Time Window</Space></Divider>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="checkin_time" label="Check-in Time *" rules={[{ required: true }]}>
                <TimePicker format="HH:mm" style={{ width: '100%' }} size="middle" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="checkout_time" label="Check-out Time *" rules={[{ required: true }]}>
                <TimePicker format="HH:mm" style={{ width: '100%' }} size="middle" />
              </Form.Item>
            </Col>
          </Row>

          {/* Live preview */}
          {(preview.checkin || preview.checkout) && (
            <div style={{
              background: '#fafafa', border: '1px solid #e8e8e8',
              borderRadius: 6, padding: '10px 14px', marginBottom: 16,
            }}>
              <div style={{ fontSize: 11, color: '#8c8c8c', marginBottom: 6 }}>Preview</div>
              <TimetableBar
                start={preview.checkin} end={preview.checkout}
                breakStart={preview.breakStart} breakEnd={preview.breakEnd}
                color={preview.color || '#1890ff'} height={10}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#bfbfbf', marginTop: 3 }}>
                <span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>24:00</span>
              </div>
              {previewNet && (
                <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <Tag color="blue"   style={{ fontSize: 11 }}>{previewNet}h net</Tag>
                  {previewIsNight && <Tag color="purple" style={{ fontSize: 11 }}>Night shift</Tag>}
                  {preview.breakStart && preview.breakEnd && (
                    <Tag color="orange" style={{ fontSize: 11 }}>
                      {toMin(preview.breakEnd) - toMin(preview.breakStart)} min break
                    </Tag>
                  )}
                </div>
              )}
            </div>
          )}

          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="late_minutes" label="Late Grace (min)" initialValue={0}>
                <Space.Compact style={{ width: '100%' }}><InputNumber min={0} max={120} size="middle" style={{ flex: 1 }} /><Input readOnly value="min" style={{ width: 44, textAlign: 'center' }} size="middle" /></Space.Compact>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="early_minutes" label="Early Exit Grace (min)" initialValue={0}>
                <Space.Compact style={{ width: '100%' }}><InputNumber min={0} max={120} size="middle" style={{ flex: 1 }} /><Input readOnly value="min" style={{ width: 44, textAlign: 'center' }} size="middle" /></Space.Compact>
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left"><Space><ClockCircleOutlined />Break (optional)</Space></Divider>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="break_time_start" label="Break Start"
                rules={[{
                  validator: (_, v) => {
                    if (v && !form.getFieldValue('break_time_end'))
                      return Promise.reject('Also set break end time');
                    return Promise.resolve();
                  },
                }]}>
                <TimePicker format="HH:mm" style={{ width: '100%' }} size="middle" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="break_time_end" label="Break End"
                dependencies={['break_time_start']}
                rules={[{
                  validator: (_, v) => {
                    const bs = form.getFieldValue('break_time_start');
                    if (!v && bs) return Promise.reject('Also set break end time');
                    if (v && bs) {
                      if (toMin(v.format('HH:mm:ss')) <= toMin(bs.format('HH:mm:ss')))
                        return Promise.reject('Break end must be after break start');
                    }
                    return Promise.resolve();
                  },
                }]}>
                <TimePicker format="HH:mm" style={{ width: '100%' }} size="middle" />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left"><Space><SettingOutlined />Flags &amp; Area</Space></Divider>
          <Row gutter={12}>
            <Col span={8}>
              <Form.Item name="must_checkin" label="Must Check-in" valuePropName="checked" initialValue={true}>
                <Switch checkedChildren="Yes" unCheckedChildren="No" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="must_checkout" label="Must Check-out" valuePropName="checked" initialValue={true}>
                <Switch checkedChildren="Yes" unCheckedChildren="No" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="is_active" label="Active" valuePropName="checked" initialValue={true}>
                <Switch checkedChildren="Yes" unCheckedChildren="No" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={12}>
            <Col span={16}>
              <Form.Item name="area_id" label="Area Restriction">
                <Select allowClear placeholder="All areas" size="middle">
                  {areas.map(a => <Option key={a.id} value={a.id}>{a.area_name || a.name}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="color" label="Color" initialValue="#1890ff">
                <Input type="color" style={{ width: '100%', height: 32 }} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Drawer>

    </div>
  );
};

export default TimetablesTab;
